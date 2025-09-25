# 💼 JobVista

<div align="center">
  <h3>Intelligent Job Portal & Career Platform</h3>
  
  <p>
    <a href="#overview">Overview</a> •
    <a href="#features">Features</a> •
    <a href="#tech-stack">Tech Stack</a> •
    <a href="#getting-started">Getting Started</a> •
    <a href="#usage">Usage</a> •
    <a href="#future">Future Roadmap</a>
  </p>
  
  <p>
    <img src="https://img.shields.io/badge/Django-5.2.3-green?style=for-the-badge&logo=django&logoColor=white" alt="Django" />
    <img src="https://img.shields.io/badge/Python-3.9-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/SQLite-3-blue?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
    <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5" />
    <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3" />
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License" />
  </p>
  
  <p>
    <a href="#getting-started"><img src="https://img.shields.io/badge/Getting%20Started-1.0.0-blue?style=for-the-badge" alt="Getting Started" /></a>
    <a href="#features"><img src="https://img.shields.io/badge/Features-15+-green?style=for-the-badge" alt="Features" /></a>
    <a href="#future"><img src="https://img.shields.io/badge/Roadmap-Active-orange?style=for-the-badge" alt="Roadmap" /></a>
  </p>
</div>

---

## 📊 Overview

JobVista is a comprehensive job portal and career platform that connects job seekers with employers through an intelligent matching system. Built with Django, the platform leverages machine learning algorithms to analyze resumes and match candidates with relevant job opportunities. The application provides a seamless experience for both job seekers and employers, featuring advanced search capabilities, application tracking, and AI-powered resume analysis.

## ✨ Features

<div align="center">
  <table>
    <tr>
      <td width="33%" style="background-color: #1a1a1a; border-radius: 10px; padding: 15px;">
        <h3>🔍 Job Search</h3>
        <ul>
          <li>Advanced job filtering</li>
          <li>AI-powered job matching</li>
          <li>Skills-based recommendations</li>
          <li>Real-time job alerts</li>
        </ul>
      </td>
      <td width="33%" style="background-color: #1a1a1a; border-radius: 10px; padding: 15px;">
        <h3>👤 User Management</h3>
        <ul>
          <li>Dual role system (Job Seeker/Company)</li>
          <li>Profile management</li>
          <li>Resume analysis with AI</li>
          <li>Application tracking</li>
        </ul>
      </td>
      <td width="33%" style="background-color: #1a1a1a; border-radius: 10px; padding: 15px;">
        <h3>🏢 Company Features</h3>
        <ul>
          <li>Job posting & management</li>
          <li>Applicant screening</li>
          <li>Company profiles</li>
          <li>Application status tracking</li>
        </ul>
      </td>
    </tr>
  </table>
</div>

## 🛠️ Tech Stack

<div align="center">
  <table>
    <tr>
      <td align="center" width="50%" style="background-color: #1a1a1a; border-radius: 10px; padding: 15px;">
        <h3>Backend</h3>
        <img src="https://img.shields.io/badge/Django-5.2.3-green?style=flat-square&logo=django&logoColor=white" alt="Django" />
        <img src="https://img.shields.io/badge/Python-3.9-blue?style=flat-square&logo=python&logoColor=white" alt="Python" />
        <img src="https://img.shields.io/badge/SQLite-3-blue?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite" />
        <img src="https://img.shields.io/badge/Pillow-11.2.1-3776AB?style=flat-square&logo=python&logoColor=white" alt="Pillow" />
        <img src="https://img.shields.io/badge/NumPy-2.2.6-013243?style=flat-square&logo=numpy&logoColor=white" alt="NumPy" />
        <img src="https://img.shields.io/badge/TensorFlow-2.16.2-FF6F00?style=flat-square&logo=tensorflow&logoColor=white" alt="TensorFlow" />
      </td>
      <td align="center" width="50%" style="background-color: #1a1a1a; border-radius: 10px; padding: 15px;">
        <h3>Frontend & Tools</h3>
        <img src="https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white" alt="HTML5" />
        <img src="https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white" alt="CSS3" />
        <img src="https://img.shields.io/badge/Bootstrap-5-7952B3?style=flat-square&logo=bootstrap&logoColor=white" alt="Bootstrap" />
        <img src="https://img.shields.io/badge/JavaScript-ES6-F7DF1E?style=flat-square&logo=javascript&logoColor=black" alt="JavaScript" />
        <img src="https://img.shields.io/badge/OpenAI-1.65.4-412991?style=flat-square&logo=openai&logoColor=white" alt="OpenAI" />
        <img src="https://img.shields.io/badge/Selenium-4.31.0-43B02A?style=flat-square&logo=selenium&logoColor=white" alt="Selenium" />
      </td>
    </tr>
  </table>
</div>

## 🚀 Getting Started

### **Prerequisites**
  - Python (v3.9 or higher)
  - pip (Python package manager)

### **Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/StoneCollector/jobvista
   cd jobvista
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser

## 📱 Usage Guide

<div align="center">
  <table>
    <tr>
      <td width="25%" style="background-color: #1a1a1a; border-radius: 10px; padding: 15px;">
        <h3>1️⃣ Sign Up</h3>
        <p>Create account as Job Seeker or Company</p>
      </td>
      <td width="25%" style="background-color: #1a1a1a; border-radius: 10px; padding: 15px;">
        <h3>2️⃣ Build Profile</h3>
        <p>Complete profile with skills and resume</p>
      </td>
      <td width="25%" style="background-color: #1a1a1a; border-radius: 10px; padding: 15px;">
        <h3>3️⃣ Search Jobs</h3>
        <p>Use filters to find relevant opportunities</p>
      </td>
      <td width="25%" style="background-color: #1a1a1a; border-radius: 10px; padding: 15px;">
        <h3>4️⃣ Apply & Track</h3>
        <p>Apply to jobs and track application status</p>
      </td>
    </tr>
  </table>
</div>

### **For Job Seekers:**
- Browse and search jobs using advanced filters
- Upload resume for AI-powered analysis
- Get personalized job recommendations
- Track application status
- Bookmark interesting positions

### **For Companies:**
- Create company profile and get approval
- Post job openings with detailed descriptions
- Review and manage applicants
- Track application status for each candidate
- Access AI-powered candidate matching

## 🔮 Future Roadmap

<div align="center">
  <table>
    <tr>
      <td width="50%" style="background-color: #1a1a1a; border-radius: 10px; padding: 15px;">
        <h3>Planned Features</h3>
        <ul>
          <li>Video Interview Integration</li>
          <li>Advanced Resume Parser</li>
          <li>Real-time Notifications</li>
          <li>Skills Assessment Tests</li>
        </ul>
      </td>
      <td width="50%" style="background-color: #1a1a1a; border-radius: 10px; padding: 15px;">
        <h3>Platform Expansion</h3>
        <ul>
          <li>Mobile Application</li>
          <li>REST API for Integrations</li>
          <li>Advanced Analytics Dashboard</li>
          <li>Multi-language Support</li>
        </ul>
      </td>
    </tr>
  </table>
</div>

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Contributors

<div align="center">
  <table>
    <tr>
      <td align="center">
        <a href="https://github.com/Yashparmar1125">
          <b>Yash Parmar</b>
        </a>
        <a href="https://github.com/Yashparmar1125">
          <b>Harshal</b>
        </a>
      </td>
    </tr>
  </table>
</div>

## 🙏 Acknowledgments

<div align="center">
  <table>
    <tr>
      <td align="center" width="33%">
        <a href="https://www.djangoproject.com/">
          <b>Django Framework</b>
        </a>
      </td>
      <td align="center" width="33%">
        <a href="https://www.tensorflow.org/">
          <b>TensorFlow</b>
        </a>
      </td>
      <td align="center" width="33%">
        <a href="https://openai.com/">
          <b>OpenAI</b>
        </a>
      </td>
    </tr>
  </table>
</div>

---

<div align="center">
  <p>Made with ❤️ by <a href="https://github.com/Yashparmar1125">Yash Parmar</a> <a href="https://github.com/StoneCollector">Harshal</a></p>
  <p>
    <a href="https://github.com/StoneCollector/jobvista">
      <img src="https://img.shields.io/github/stars/StoneCollector/jobvista?style=social" alt="GitHub Stars" />
    </a>
    <a href="https://github.com/StoneCollector/jobvista/fork">
      <img src="https://img.shields.io/github/forks/StoneCollector/jobvista?style=social" alt="GitHub Forks" />
    </a>
    <a href="https://github.com/StoneCollector/jobvista/issues">
      <img src="https://img.shields.io/github/issues/StoneCollector/jobvista?style=social" alt="GitHub Issues" />
    </a>
  </p>
</div>
