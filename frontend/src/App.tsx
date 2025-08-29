import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { SearchPage } from './pages/SearchPage';
import { SearchResult } from './pages/SearchResult';
import Header from './components/Header';
import Home from './components/Home';
import VetsContact from './components/VetsContact';
import AboutUs from './components/AboutUs';

const App = () => {
  return (
    <Router>
      <div className="min-h-screen bg-white">
        <Header />
        <Routes>
          {/* Original Routes - RESTORED */}
          <Route path="/" element={<Home />} />
          <Route path="/vets" element={<VetsContact />} />
          <Route path="/about" element={<AboutUs />} />
          
          {/* New RAG Search Routes - ADDED */}
          <Route path="/rag" element={<SearchPage />} />
          <Route path="/rag/search" element={<SearchPage />} />
          <Route path="/rag/search/:searchId" element={<SearchResult />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;