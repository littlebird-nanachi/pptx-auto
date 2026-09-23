import copy
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
from pptxgen.theme import resolve_logo, load_theme
from pptxgen.schemas import validate
from pptxgen.renderer import render_html, ROOT
from pptxgen.pipeline import generate, launch_browser, inspect_page

DATA = json.loads((ROOT/'examples/phase1.json').read_text())

class ThemeTests(unittest.TestCase):
    def test_fallback_override_corrupt_missing(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'assets').mkdir(); (root/'themes'/'client').mkdir(parents=True)
            Image.new('RGB',(200,50)).save(root/'assets/logo.png')
            self.assertEqual(resolve_logo(root,'client').width,200)
            Image.new('RGB',(100,100)).save(root/'themes/client/logo.png')
            self.assertEqual(resolve_logo(root,'client').width,100)
            (root/'themes/client/logo.png').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'LOGO_LOAD_ERROR'): resolve_logo(root,'client')
            (root/'assets/logo.png').unlink()
            with self.assertRaisesRegex(ValueError,'LOGO_LOAD_ERROR'): resolve_logo(root,'default')
            with self.assertRaises(ValueError): resolve_logo(root,'../client')

    def test_schema(self):
        validate(DATA)
        invalid=copy.deepcopy(DATA); invalid['slides'][0]['layout']='unknown'
        with self.assertRaises(Exception): validate(invalid)
        invalid=copy.deepcopy(DATA); invalid['slides'][1]['slide_number']=9
        with self.assertRaises(ValueError): validate(invalid)

    def test_missing_logo_report_and_no_output(self):
        with tempfile.TemporaryDirectory() as d:
            report=generate(ROOT/'examples/phase1.json',Path(d)/'out',root=Path(d))
            self.assertFalse(report['generated'])
            self.assertIn('LOGO_LOAD_ERROR',report['issues'][0]['detail'])
            self.assertTrue((Path(d)/'out/qa_report.json').exists())
            self.assertFalse((Path(d)/'out/presentation.pptx').exists())

class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw=sync_playwright().start()
        cls.browser=launch_browser(cls.pw)
        cls.logo, cls.theme=load_theme(ROOT,'default')

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.pw.stop()

    def render(self,slide,width=1920,logo=None):
        page=self.browser.new_page(viewport={'width':width,'height':1080})
        self.addCleanup(page.close)
        page.set_content(render_html(slide,DATA['presentation'],3,logo or self.logo,self.theme,width,1080))
        return page

    def test_all_layouts_and_ratios(self):
        for width in (1920,1440):
            for slide in DATA['slides']:
                with self.subTest(width=width,layout=slide['layout']):
                    result=inspect_page(self.render(slide,width))
                    self.assertEqual(result['issues'],[])
                    self.assertAlmostEqual(result['logo']['width']/result['logo']['height'],self.logo.width/self.logo.height,places=2)

    def test_long_title(self):
        slide=copy.deepcopy(DATA['slides'][0]); slide['title']='長いタイトルでもロゴのセーフエリアを守りながら複数行へ折り返して表示します'
        self.assertEqual(inspect_page(self.render(slide))['issues'],[])

    def test_qa_detects_regressions(self):
        cases=[
            ("document.querySelector('.slide-logo').remove()",'LOGO_COUNT'),
            ("document.querySelector('.slide-logo').src='data:image/png;base64,broken'",'LOGO_LOAD'),
            ("document.querySelector('.slide-logo').style.left='0px'",'LOGO_POSITION'),
            ("document.querySelector('.slide-logo').style.width='400px'",'LOGO_ASPECT_RATIO'),
            ("document.querySelector('.slide-logo').style.display='none'",'LOGO_VISIBLE'),
            ("Object.assign(document.querySelector('h1').style,{position:'absolute',right:'64px',top:'40px'})",'LOGO_TEXT_OVERLAP'),
            ("Object.assign(document.querySelector('.main-content').style,{position:'absolute',right:'64px',top:'40px',margin:'0px'})",'LOGO_OVERLAP'),
        ]
        for script,code in cases:
            with self.subTest(code=code):
                page=self.render(DATA['slides'][1]); page.evaluate(script)
                self.assertIn(code,[i['code'] for i in inspect_page(page)['issues']])

    def test_theme_logo_ratios(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'assets').mkdir()
            for size in ((80,160),(400,40)):
                Image.new('RGB',size).save(root/'assets/logo.png')
                logo=resolve_logo(root,'default')
                self.assertEqual(inspect_page(self.render(DATA['slides'][0],logo=logo))['issues'],[])

class PipelineTests(unittest.TestCase):
    def test_overflow_blocks_export(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); data=copy.deepcopy(DATA); data['slides'][0]['title']='非常に長いタイトル' * 300
            inp=root/'input.json'; inp.write_text(json.dumps(data))
            report=generate(inp,root/'out')
            self.assertFalse(report['generated'])
            self.assertTrue(report['slides'][0]['issues'])
            self.assertFalse((root/'out/presentation.pptx').exists())

if __name__=='__main__': unittest.main()
