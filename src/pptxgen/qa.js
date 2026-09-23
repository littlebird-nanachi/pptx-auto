() => {
  const issues = [];
  const add = (code, detail) => issues.push({severity:'error', code, detail});
  const slide = document.querySelector('.slide');
  const rect = e => e.getBoundingClientRect();
  const root = rect(slide);
  const intersects = (a,b) => a.left < b.right-0.5 && a.right > b.left+0.5 && a.top < b.bottom-0.5 && a.bottom > b.top+0.5;
  const outside = (a,b) => a.left < b.left-1 || a.top < b.top-1 || a.right > b.right+1 || a.bottom > b.bottom+1;
  const style = getComputedStyle(slide);
  const token = name => parseFloat(style.getPropertyValue(name));
  const logos = [...document.querySelectorAll('.slide-logo')];
  if (logos.length !== 1) add('LOGO_COUNT', `Expected 1, got ${logos.length}`);
  const logo = logos[0];
  if (logo) {
    const r = rect(logo), s = getComputedStyle(logo);
    if (!logo.complete || !logo.naturalWidth || !logo.naturalHeight) add('LOGO_LOAD', 'Logo failed to decode');
    if (s.display === 'none' || s.visibility !== 'visible' || +s.opacity === 0 || r.width <= 0 || r.height <= 0)
      add('LOGO_VISIBLE', 'Logo must be visible');
    if (Math.abs(r.top-root.top-token('--logo-top')) > 1 || Math.abs(root.right-r.right-token('--logo-right')) > 1 ||
        Math.abs(r.height-token('--logo-height')) > 1 || outside(r,root)) add('LOGO_POSITION', 'Logo is outside configured top-right region');
    if (Math.abs(r.width/r.height-logo.naturalWidth/logo.naturalHeight) > 0.005) add('LOGO_ASPECT_RATIO', 'Logo aspect ratio changed');
    for (const el of document.querySelectorAll('.slide-heading, .main-content, .main-content *, .footer')) {
      if (intersects(r,rect(el))) add('LOGO_OVERLAP', `Logo overlaps ${el.className || el.tagName}`);
    }
  }
  if (!document.querySelector('h1')?.textContent.trim()) add('TITLE_MISSING','Missing title');
  const footerEl = document.querySelector('.footer');
  const footer = footerEl ? rect(footerEl) : null;
  for (const el of slide.querySelectorAll('*')) {
    if (['HEADER'].includes(el.tagName)) continue;
    const r = rect(el);
    if (r.width && r.height && outside(r,root)) add('SLIDE_OVERFLOW', el.className || el.tagName);
    // Browsers report table row scroll dimensions differently from their laid-out
    // cells; text ranges below remain the authoritative overflow check.
    if (!['TABLE','THEAD','TBODY','TR'].includes(el.tagName) &&
        (el.scrollWidth > el.clientWidth+1 || el.scrollHeight > el.clientHeight+1)) add('ELEMENT_OVERFLOW',el.className || el.tagName);
    if (footer && el.matches('.slide-heading,.main-content') && intersects(r,footer)) add('FOOTER_OVERLAP',el.className);
  }
  const runs = [];
  const walker = document.createTreeWalker(slide, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode;
    if (!n.textContent.trim()) continue;
    const parent = n.parentElement;
    if (parseFloat(getComputedStyle(parent).fontSize) < token('--minimum-font-size')) add('SMALL_TEXT',parent.tagName);
    const range = document.createRange(); range.selectNodeContents(n);
    for (const r of range.getClientRects()) {
      if (outside(r,root)) add('TEXT_OVERFLOW',n.textContent.slice(0,60));
      if (logo && intersects(r,rect(logo))) add('LOGO_TEXT_OVERLAP',n.textContent.slice(0,60));
      runs.push({r,n});
    }
  }
  for (let i=0;i<runs.length;i++) for(let j=i+1;j<runs.length;j++) {
    if(runs[i].n !== runs[j].n && intersects(runs[i].r,runs[j].r)) add('TEXT_OVERLAP',runs[i].n.textContent.slice(0,60));
  }
  return {issues, logo: logo ? {naturalWidth:logo.naturalWidth,naturalHeight:logo.naturalHeight,
    x:rect(logo).x,y:rect(logo).y,width:rect(logo).width,height:rect(logo).height}: null};
}
