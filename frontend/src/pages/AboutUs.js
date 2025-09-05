// src/pages/AboutUs.js
import React from "react";
import "./AboutUs.css"; // ✅ optional separate CSS if you want custom styles

const AboutUs = () => {
  return (
    <div className="about-container">
      <h1 className="about-title">About Us</h1>
      <p className="about-text">
        Welcome to <span className="highlight">AI Debug</span>, your
        AI-powered debugging companion. Our mission is to help developers find
        and fix bugs smarter and faster with real-time insights and code
        suggestions.
      </p>

      <p className="about-text">
        Whether you’re a beginner learning to code or an experienced developer
        working on large projects, our platform provides intelligent
        recommendations, performance optimizations, and bug detection powered by
        AI.
      </p>

      <p className="about-text">
        We believe in making coding easier, more efficient, and accessible to
        everyone. 🚀
      </p>

      <div className="about-footer">
        <p>📩 Contact us: support@aidebug.com</p>
       <p>
    🌐 Visit:{" "}
    <a 
      href="https://github.com/bhola-dev58" 
      target="_blank" 
      rel="noopener noreferrer"
    >
      github.com/bhola-dev58
    </a>
  </p>
      </div>
    </div>
  );
};

export default AboutUs;
