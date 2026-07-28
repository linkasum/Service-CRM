import { createRoot } from 'react-dom/client';
import App from './App';
import { getTheme } from './hooks/useTheme';
import './styles.css';

// Apply saved theme before render
document.documentElement.setAttribute('data-theme', getTheme());

createRoot(document.getElementById('root')!).render(<App />);
