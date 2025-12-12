# GitHub Wiki Initialization Guide

## Manual Steps Required

GitHub Wiki is a separate git repository and cannot be fully automated via API.
Follow these steps to initialize it:

### 1. Enable Wiki
1. Go to your repository on GitHub
2. Click Settings → Features
3. Check ✅ "Wikis"

### 2. Create Home Page
1. Go to Wiki tab in your repository
2. Click "Create the first page"
3. Title: "Home"
4. Copy the content below:

---

# Ans Project Documentation

Welcome to the Ans project documentation. Ans is a Snapchat fact-checking service for Amsterdam youth.

## Quick Links
- [[Getting Started]]
- [[Architecture]]
- [[Agent Workflows]]
- [[Testing Standards]]

## For New Developers
1. Read [[Development Setup]]
2. Review [[Architecture Overview]]
3. Check [[Contributing Guidelines]]
4. Join the team on GitHub

## Project Overview
Ans allows youth to submit questionable content via Snapchat DM for fact-checking. The system combines AI analysis (OpenAI) with human verification through a volunteer network.

### Tech Stack
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0
- Frontend: Svelte 5, TypeScript, Vite
- Database: PostgreSQL with pgvector
- AI: OpenAI API
- Infrastructure: Docker on Hetzner VPS

### Repository Structure
- `/backend` - FastAPI application
- `/frontend` - Svelte application
- `/ai-service` - OpenAI integration service
- `/infrastructure` - Docker and deployment configs
- `/docs/adr` - Architecture Decision Records
- `/docs/agents` - Agent role definitions

---

### 3. Create Additional Pages

Create these pages (leave content as placeholder for now):

**Getting Started**
- Development Setup
- Running Tests
- Deployment Guide

**Architecture**
- System Overview
- ADR Index
- Database Schema
- API Documentation

**Agent Workflows**
- Backend Development Guide
- Frontend Development Guide
- AI/ML Development Guide
- Testing Standards

**Testing Standards**
- TDD Guidelines
- Coverage Requirements
- Test Types and Structure

### 4. Clone Wiki for Local Editing (Optional)

```bash
# Clone the wiki repository
git clone https://github.com/YOUR-ORG/ans-project.wiki.git

# Add pages
cd ans-project.wiki
# Edit .md files
git add .
git commit -m "Add initial documentation"
git push
```

## Wiki Maintenance

- Agents should update Wiki when making architectural changes
- System Architect maintains Architecture section
- Database Architect maintains Database Schema
- DevOps maintains Getting Started guides
