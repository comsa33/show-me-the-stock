import React from 'react';
import { Mail, Github, Linkedin, Heart } from 'lucide-react';
import './Footer.css';

const Footer: React.FC = () => {
  return (
    <footer className="footer">
      <div className="footer-content">
        <div className="footer-section">
          <h3 className="footer-title">ShowMeTheStock</h3>
          <p className="footer-desc">AI-powered stock analysis platform</p>
        </div>
        
        <div className="footer-section">
          <h4 className="section-title">Contact</h4>
          <div className="contact-info">
            <div className="contact-item">
              <Mail size={16} />
              <a href="mailto:comsa333@gmail.com">comsa333@gmail.com</a>
            </div>
            <div className="contact-item">
              <Github size={16} />
              <a href="https://github.com/comsa33" target="_blank" rel="noopener noreferrer">
                comsa33
              </a>
            </div>
            <div className="contact-item">
              <Linkedin size={16} />
              <a href="https://www.linkedin.com/in/ruo-lee-79864522a/" target="_blank" rel="noopener noreferrer">
                Ruo Lee
              </a>
            </div>
          </div>
        </div>
        
        <div className="footer-section">
          <h4 className="section-title">Developer</h4>
          <p className="developer-name">이루오 (Ruo Lee)</p>
          <p className="developer-role">AI Developer</p>
        </div>
      </div>
      
      <div className="footer-bottom">
        <div className="footer-bottom-content">
          <p>
            Made with <Heart size={14} className="heart-icon" /> by Ruo Lee
          </p>
          <p className="copyright">
            © {new Date().getFullYear()} ShowMeTheStock. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;