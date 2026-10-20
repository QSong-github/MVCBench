(() => {
  'use strict';

  const menu = document.getElementById('menu-toggle');
  const nav = document.getElementById('site-nav');
  if (menu && nav) {
    const closeMenu = () => {
      nav.classList.remove('is-open');
      menu.setAttribute('aria-expanded', 'false');
    };
    menu.addEventListener('click', () => {
      const isOpen = nav.classList.toggle('is-open');
      menu.setAttribute('aria-expanded', String(isOpen));
    });
    nav.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape') closeMenu();
    });
    window.addEventListener('resize', () => {
      if (window.innerWidth > 900) closeMenu();
    });
  }

  const tabs = Array.from(document.querySelectorAll('[data-stage][role="tab"]'));
  const selectStage = (index, focus = false) => {
    tabs.forEach((tab, i) => {
      const active = i === index;
      tab.classList.toggle('is-active', active);
      tab.setAttribute('aria-selected', String(active));
      tab.tabIndex = active ? 0 : -1;
      const panel = document.getElementById(tab.getAttribute('aria-controls'));
      if (panel) panel.hidden = !active;
    });
    if (focus && tabs[index]) tabs[index].focus();
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectStage(index));
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % tabs.length;
      else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index - 1 + tabs.length) % tabs.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = tabs.length - 1;
      if (next !== undefined) { event.preventDefault(); selectStage(next, true); }
    });
  });

  const dialog = document.getElementById('figure-dialog');
  const dialogImage = document.getElementById('dialog-image');
  const dialogLabel = document.getElementById('dialog-label');
  const closeDialog = document.getElementById('dialog-close');
  let previousFocus = null;
  if (dialog && dialogImage && typeof dialog.showModal === 'function') {
    document.querySelectorAll('[data-lightbox]').forEach(button => {
      button.addEventListener('click', () => {
        previousFocus = button;
        const source = button.getAttribute('data-lightbox');
        const thumbnail = button.querySelector('img');
        if (!source || !thumbnail) return;
        dialogImage.src = source;
        dialogImage.alt = thumbnail.alt;
        dialogLabel.textContent = thumbnail.alt.replace(/^Figure\s*\d+\s*/i, '') || 'MVCBench figure';
        dialog.showModal();
        closeDialog?.focus();
      });
    });
    const hideDialog = () => dialog.close();
    closeDialog?.addEventListener('click', hideDialog);
    dialog.addEventListener('click', event => {
      if (event.target === dialog) hideDialog();
    });
    dialog.addEventListener('close', () => {
      dialogImage.removeAttribute('src');
      if (previousFocus && previousFocus.isConnected) previousFocus.focus();
    });
  }

  document.querySelectorAll('[data-copy-target]').forEach(button => {
    const normalLabel = button.textContent;
    button.addEventListener('click', async () => {
      const target = document.getElementById(button.dataset.copyTarget);
      if (!target) return;
      const content = target.innerText;
      try {
        if (!navigator.clipboard?.writeText) throw new Error('Clipboard API unavailable');
        await navigator.clipboard.writeText(content);
        button.textContent = 'Copied ✓';
      } catch (error) {
        // Some browser/file contexts do not grant clipboard access.
        button.textContent = 'Select text to copy';
        const range = document.createRange();
        range.selectNodeContents(target);
        window.getSelection()?.removeAllRanges();
        window.getSelection()?.addRange(range);
      }
      window.setTimeout(() => { button.textContent = normalLabel; }, 2000);
    });
  });

  // Non-essential active-section highlighting. Content remains usable without this API.
  if ('IntersectionObserver' in window) {
    const links = Array.from(document.querySelectorAll('#site-nav a[href^="#"]'));
    const byId = new Map(links.map(link => [link.getAttribute('href').slice(1), link]));
    const observer = new IntersectionObserver(entries => {
      entries.filter(entry => entry.isIntersecting).forEach(entry => {
        links.forEach(link => link.classList.toggle('active', link === byId.get(entry.target.id)));
      });
    }, { rootMargin: '-22% 0px -66% 0px', threshold: 0 });
    byId.forEach((_, id) => { const el = document.getElementById(id); if (el) observer.observe(el); });
  }
})();
