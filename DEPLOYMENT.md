# Deployment Guide

This guide covers deploying the AI Code Review Agent to Streamlit Cloud.

## Prerequisites

1. OpenAI API key
2. GitHub account
3. This repository pushed to GitHub

## Step 1: Prepare Your Repository

### 1.1 Initialize Git (if not already done)

```bash
git init
git add .
git commit -m "Initial commit: AI Code Review Agent"
```

### 1.2 Create GitHub Repository

1. Go to [github.com](https://github.com) and create a new repository
2. Name it something like `ai-code-review-agent`
3. Make it public (required for Streamlit Cloud free tier)
4. Don't initialize with README (we already have one)

### 1.3 Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/ai-code-review-agent.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy to Streamlit Cloud

### 2.1 Go to Streamlit Cloud

Visit [share.streamlit.io](https://share.streamlit.io)

### 2.2 Create New App

1. Click "New app"
2. Sign in with your GitHub account
3. Select your repository
4. Set the main file path to `app.py`
5. Click "Deploy"

### 2.3 Add Secrets

1. After deployment, go to your app settings
2. Click "Secrets" or "Environment Variables"
3. Add the following secret:

```
OPENAI_API_KEY=your_actual_api_key_here
```

4. (Optional) Add GitHub token if you want PR commenting:

```
GITHUB_TOKEN=your_github_token_here
```

### 2.4 Redeploy

After adding secrets, click "Redeploy" to apply the changes.

## Step 3: Test Your Deployment

1. Open your deployed app URL
2. Enter the repository URL you want to review
3. Click "Start Code Review"
4. Verify that the review completes successfully

## Alternative: HuggingFace Spaces

### 3.1 Create Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click "Create new Space"
3. Choose "Streamlit" as the SDK
4. Name your space

### 3.2 Upload Files

Either:
- Clone the space and push your code
- Or use the web interface to upload files

### 3.3 Add Secrets

1. Go to Space Settings → Secrets
2. Add `OPENAI_API_KEY`
3. (Optional) Add `GITHUB_TOKEN`

### 3.4 Deploy

The space will automatically build and deploy.

## Troubleshooting

### Issue: "Module not found" errors

**Solution**: Make sure `requirements.txt` is in the root directory and includes all dependencies.

### Issue: API key not working

**Solution**: 
- Verify the secret is set correctly in Streamlit Cloud
- Make sure you're using the correct environment variable name
- Check that your OpenAI API key has credits

### Issue: Repository cloning fails

**Solution**:
- Ensure the repository is public
- Check that the URL format is correct
- Verify GitPython is installed

### Issue: App crashes on large repositories

**Solution**:
- Use the "Max Files" limit in the sidebar
- Consider using a smaller repository for testing
- Check your OpenAI API rate limits

## Cost Estimation

For a typical repository review:

- Small repo (<10 files): ~$0.01-0.05
- Medium repo (10-50 files): ~$0.05-0.25
- Large repo (50-200 files): ~$0.25-1.00

Costs depend on:
- Number of files
- Code complexity
- Number of chunks needed
- Model used (gpt-4o-mini vs gpt-4o)

## Monitoring

### Check Logs

In Streamlit Cloud:
1. Go to your app
2. Click "Logs" in the sidebar
3. View real-time logs

### Monitor API Usage

Check your OpenAI dashboard to monitor:
- Token usage
- Costs
- Rate limits

## Security Best Practices

1. **Never commit API keys** to your repository
2. **Use environment variables** for all secrets
3. **Rotate API keys** regularly
4. **Monitor usage** for unusual activity
5. **Set rate limits** on your OpenAI account

## Demo Recording Tips

For the 2-minute screen recording:

1. **Prepare**: Have a test repository ready (small, public)
2. **Show features**:
   - Enter API key
   - Input repository URL
   - Start review
   - Show progress
   - Display results with filtering
   - Show confidence scoring
   - Download results
3. **Keep it concise**: Focus on the key features
4. **Use good audio**: Clear narration
5. **Highlight**: Point out the confidence scoring feature

## Recommended Test Repositories

For demo purposes, use small, well-known repositories:

- https://github.com/octocat/Hello-World (very small)
- https://github.com/python/cpython (large - use max_files limit)
- https://github.com/pallets/flask (medium)
- Your own small project

## Success Criteria

Your deployment is successful when:

- ✅ App loads without errors
- ✅ Can enter API key in sidebar
- ✅ Can review a GitHub repository
- ✅ Results display correctly
- ✅ Filtering works
- ✅ Download buttons work
- ✅ Confidence scoring is visible
- ✅ Low-confidence comments are flagged
