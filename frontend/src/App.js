import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from 'sonner';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import QuickLinks from './components/QuickLinks';
import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import CommitteePage from './pages/CommitteePage';
import ProgramPage from './pages/ProgramPage';
import SpeakersPage from './pages/SpeakersPage';
import RegistrationPage from './pages/RegistrationPage';
import AccommodationPage from './pages/AccommodationPage';
import SponsorsPage from './pages/SponsorsPage';
import VenuePage from './pages/VenuePage';
import ContactPage from './pages/ContactPage';
import DownloadsPage from './pages/DownloadsPage';

function App() {
  return (
    <div className="App">
      <Toaster 
        position="top-right" 
        richColors 
        closeButton
        toastOptions={{
          style: {
            fontFamily: 'Manrope, sans-serif',
          },
        }}
      />
      <BrowserRouter>
        <Navbar />
        <QuickLinks />
        <main className="min-h-screen">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/committee" element={<CommitteePage />} />
            <Route path="/program" element={<ProgramPage />} />
            <Route path="/speakers" element={<SpeakersPage />} />
            <Route path="/registration" element={<RegistrationPage />} />
            <Route path="/accommodation" element={<AccommodationPage />} />
            <Route path="/sponsors" element={<SponsorsPage />} />
            <Route path="/venue" element={<VenuePage />} />
            <Route path="/contact" element={<ContactPage />} />
            <Route path="/downloads" element={<DownloadsPage />} />
          </Routes>
        </main>
        <Footer />
      </BrowserRouter>
    </div>
  );
}

export default App;
