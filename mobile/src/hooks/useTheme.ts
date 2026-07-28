export function getTheme(): 'light' | 'dark' {
  return (localStorage.getItem('theme') as 'light' | 'dark') || 'light';
}

export function setTheme(theme: 'light' | 'dark') {
  localStorage.setItem('theme', theme);
  document.documentElement.setAttribute('data-theme', theme);
}

export function toggleTheme(): 'light' | 'dark' {
  const next = getTheme() === 'light' ? 'dark' : 'light';
  setTheme(next);
  return next;
}
