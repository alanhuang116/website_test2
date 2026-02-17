# Quick Deployment Guide

## 🚀 Deploy Your VOC Portal in 5 Minutes

### Method 1: Streamlit Cloud (Easiest - FREE)

**Perfect for sharing with colleagues and public demos**

#### Step 1: Prepare Your Code

```bash
# Navigate to your project
cd "D:\Ayodeji Project Data"

# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - VOC Geospatial Portal"
```

#### Step 2: Push to GitHub

1. Go to [GitHub.com](https://github.com) and create a new repository
   - Name it: `voc-geospatial-portal`
   - Make it Public (for free Streamlit hosting)
   - Don't initialize with README (you already have one)

2. Push your code:
```bash
git remote add origin https://github.com/YOUR_USERNAME/voc-geospatial-portal.git
git branch -M main
git push -u origin main
```

#### Step 3: Deploy on Streamlit Cloud

1. Visit [share.streamlit.io](https://share.streamlit.io)
2. Click "Sign in with GitHub"
3. Click "New app"
4. Fill in:
   - **Repository**: `YOUR_USERNAME/voc-geospatial-portal`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. Click "Deploy!"

#### Step 4: Share Your Portal!

After 2-3 minutes, your portal will be live at:
```
https://YOUR_USERNAME-voc-geospatial-portal.streamlit.app
```

**That's it!** 🎉 Share this URL with anyone.

---

## Method 2: Docker (Full Control)

**Perfect for self-hosting or enterprise deployment**

```bash
# Build the Docker image
docker build -t voc-portal .

# Run the container
docker run -p 8501:8501 voc-portal

# Access at: http://localhost:8501
```

**Deploy to cloud**:
- **AWS ECS**: Use the Docker image
- **Google Cloud Run**: `gcloud run deploy`
- **Azure Container Instances**: `az container create`

---

## Method 3: Local Network

**Perfect for team/office access**

1. Run the app:
```bash
streamlit run app.py --server.address=0.0.0.0
```

2. Find your IP:
```bash
# Windows
ipconfig

# Mac/Linux
ifconfig | grep "inet "
```

3. Share with your team:
```
http://YOUR_IP:8501
Example: http://192.168.1.100:8501
```

---

## Troubleshooting

### Issue: "Module not found" on Streamlit Cloud
**Solution**: Make sure `requirements.txt` is in the root directory and all dependencies are listed.

### Issue: Census tract download fails
**Solution**: Streamlit Cloud has internet access. The first run will download census data (~30 seconds). Subsequent runs will use cached data.

### Issue: App is slow
**Solution**:
- Streamlit Cloud has resource limits (1 GB RAM)
- Reduce grid resolution in Advanced Settings
- Use faster interpolation methods (IDW instead of Kriging)

### Issue: App keeps sleeping
**Solution**: Free tier apps sleep after 7 days of inactivity. They wake up automatically when accessed (takes ~30 seconds).

---

## Security Tips

### For Public Deployment:

1. **Don't commit sensitive data** - Add to `.gitignore`:
   ```
   .env
   data/sensitive_*.xlsx
   ```

2. **Add basic authentication** (optional):
   - Use Streamlit's built-in authentication
   - Or add simple password protection (see README)

3. **Use environment variables** for API keys:
   ```python
   import os
   API_KEY = os.environ.get('API_KEY')
   ```

### For Private Deployment:

1. Set repository to **Private** on GitHub
2. Invite collaborators who need access
3. Streamlit Cloud supports private repos

---

## Cost Comparison

| Platform | Free Tier | Paid Plans |
|----------|-----------|------------|
| **Streamlit Cloud** | ✅ Unlimited public apps | $20/mo for private apps |
| **Heroku** | ❌ (removed) | $7/mo Basic Dyno |
| **AWS EC2** | ✅ 12 months (t2.micro) | ~$10/mo (t3.medium) |
| **Google Cloud Run** | ✅ 2M requests/month | Pay per use |
| **Local Network** | ✅ Always free | - |

---

## Recommended Approach

### For Research/Academic Use:
👉 **Streamlit Cloud** (Public repo)
- Free
- Easy to share with reviewers
- Include in publications

### For Internal Team Use:
👉 **Local Network** or **Private Streamlit Cloud**
- No cost for local
- Full control

### For Production/Enterprise:
👉 **Docker on AWS/Azure/GCP**
- Scalable
- Reliable
- Custom domain support

---

## Next Steps

After deployment:

1. **Add to your paper/website**: Include the portal URL
2. **Monitor usage**: Streamlit Cloud provides analytics
3. **Update easily**: Just `git push` to deploy updates
4. **Get feedback**: Share with colleagues and iterate

---

## Support

- **Streamlit Docs**: https://docs.streamlit.io/
- **Deployment Help**: https://docs.streamlit.io/streamlit-community-cloud
- **Community Forum**: https://discuss.streamlit.io/

Good luck with your deployment! 🚀
