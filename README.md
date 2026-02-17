# VOC Geospatial Visualization Portal

Interactive spatial analysis portal for Volatile Organic Compounds (VOC) monitoring data.

## Features

- 🗺️ **Interactive Geospatial Maps** - Visualize VOC concentrations across census tracts
- 🔄 **Multiple Interpolation Methods** - Choose from IDW, Kriging, RBF, and more
- 🎨 **Modern UI** - Beautiful gradient design with smooth animations
- 📊 **Statistical Analysis** - Real-time statistics and distribution plots
- 🔍 **Advanced Filtering** - Filter by compound, city, round, and date
- 📈 **Temporal Trends** - Track changes over time
- 📥 **Data Export** - Download processed data as CSV

## Interpolation Methods

1. **IDW (Inverse Distance Weighting)** - Classic spatial interpolation
2. **Ordinary Kriging** - Geostatistical method with variogram modeling
3. **Universal Kriging** - Advanced kriging with trend modeling
4. **RBF (Radial Basis Functions)** - Multiple kernel options (Multiquadric, Gaussian, Thin Plate, Linear)
5. **Linear/Cubic Interpolation** - Fast polynomial methods
6. **Nearest Neighbor** - Simple proximity-based interpolation

## Installation

### Prerequisites
- Python 3.11+
- Conda (recommended) or pip

### Steps

1. **Install dependencies:**
```bash
conda run -n base pip install -r requirements.txt
```

Or with pip directly:
```bash
pip install -r requirements.txt
```

2. **Ensure data file is present:**
- Place `VOC_cleanTract.xlsx` in the `data/` directory

## Usage

### Launch the application:

```bash
streamlit run app.py
```

Or with conda:
```bash
conda run -n base streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

### Using the Portal

1. **Select Compound** - Choose from 62 VOC compounds in the sidebar
2. **Choose Interpolation Method** - Select your preferred spatial interpolation algorithm
3. **Adjust Settings** - Fine-tune grid resolution and method parameters
4. **Apply Filters** - Filter by city, measurement round, or date range
5. **Explore Results** - View interpolated surface, statistics, and time trends
6. **Compare Methods** - Use the Method Comparison tab to evaluate different algorithms
7. **Export Data** - Download aggregated results as CSV

## Project Structure

```
D:\Ayodeji Project Data\
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── config.py                   # Configuration settings
├── README.md                   # This file
│
├── data/
│   ├── VOC_cleanTract.xlsx    # Input data
│   └── census_tracts.geojson  # Cached census geometries
│
├── src/
│   ├── geocoding.py           # Census tract geocoding
│   ├── data_loader.py         # Data loading and processing
│   ├── interpolation.py       # Interpolation engine
│   └── visualization.py       # Plotly visualization functions
│
└── assets/
    └── styles.css             # Custom CSS styling
```

## Data Information

- **Total Records**: 9,261 VOC measurements
- **Census Tracts**: 38 tracts in Jefferson County, TX
- **Cities**: Beaumont, Port Arthur
- **Compounds**: 62 different VOCs
- **Measurement Rounds**: 6 rounds
- **Date Range**: November 2024

## Technical Details

### Spatial Interpolation

The portal uses census tract centroids as sample points for interpolation. Multiple measurements per tract are aggregated using:
- Mean (default)
- Median (robust to outliers)
- Maximum (worst-case scenario)
- 95th percentile

### Color Scaling

To handle extreme outliers (max values 5000x larger than median), the portal uses:
- Percentile-based scaling (5th-95th percentile by default)
- Optional logarithmic scale
- Robust gradient color mapping (Red-Yellow-Green)

### Census Tract Data

Census tract geometries are automatically downloaded from the US Census Bureau's Tiger/Line shapefiles on first run and cached locally for performance.

## Troubleshooting

### Issue: "Module not found" errors
**Solution**: Reinstall dependencies
```bash
conda run -n base pip install -r requirements.txt --force-reinstall
```

### Issue: Census tract download fails
**Solution**: Check internet connection or manually download shapefiles from:
https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_48_tract.zip

### Issue: Kriging methods not available
**Solution**: Ensure PyKrige is installed:
```bash
pip install pykrige
```

### Issue: Application is slow
**Solution**:
- Reduce grid resolution in Advanced Settings
- Use faster interpolation methods (IDW, Linear) instead of Kriging
- Filter data to fewer rounds/cities

## Performance Tips

- **Grid Resolution**: Lower values (50-75) for quick previews, higher (150-200) for publication-quality maps
- **Method Selection**: IDW and RBF are faster than Kriging for large datasets
- **Data Filtering**: Reduce data volume by filtering specific compounds, cities, or rounds

---

## 🚀 Deployment Guide

Deploy your VOC Geospatial Portal so others can access it over the internet.

### Option 1: Streamlit Community Cloud (Recommended - FREE)

**Best for**: Sharing with colleagues, public demos, research presentations

**Steps**:

1. **Create a GitHub Repository**
   ```bash
   cd "D:\Ayodeji Project Data"
   git init
   git add .
   git commit -m "Initial commit - VOC Geospatial Portal"
   ```

2. **Push to GitHub**
   - Create a new repository on [GitHub.com](https://github.com/new)
   - Follow GitHub's instructions to push your code:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/voc-portal.git
   git branch -M main
   git push -u origin main
   ```

3. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository: `YOUR_USERNAME/voc-portal`
   - Main file path: `app.py`
   - Click "Deploy"

4. **Your Portal is Live!**
   - Streamlit will provide a URL like: `https://YOUR_USERNAME-voc-portal.streamlit.app`
   - Share this URL with anyone!

**Pros**:
- ✅ Free for public repositories
- ✅ Automatic SSL/HTTPS
- ✅ Auto-deploys on git push
- ✅ No server management

**Cons**:
- ⚠️ Limited resources (1 GB RAM)
- ⚠️ App sleeps after inactivity (wakes on access)

---

### Option 2: Docker Deployment

**Best for**: Self-hosting, enterprise deployment, full control

**1. Create Dockerfile** (already in project):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**2. Build and Run**:

```bash
# Build Docker image
docker build -t voc-portal .

# Run container
docker run -p 8501:8501 voc-portal

# Or run with data volume
docker run -p 8501:8501 -v $(pwd)/data:/app/data voc-portal
```

**3. Access**: `http://localhost:8501` or `http://YOUR_SERVER_IP:8501`

**Deploy to Cloud**:
- **AWS**: Use ECS/Fargate or EC2
- **Azure**: Use Azure Container Instances
- **Google Cloud**: Use Cloud Run

---

### Option 3: Heroku Deployment

**Best for**: Quick cloud deployment with custom domain support

**Steps**:

1. **Create `setup.sh`**:
```bash
mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

2. **Create `Procfile`**:
```
web: sh setup.sh && streamlit run app.py
```

3. **Create `runtime.txt`**:
```
python-3.11
```

4. **Deploy**:
```bash
heroku login
heroku create voc-portal
git push heroku main
heroku open
```

**Cost**: Free tier available, then $7/month for Basic

---

### Option 4: AWS EC2 (Self-Hosted Cloud)

**Best for**: Full control, production deployments

**Steps**:

1. **Launch EC2 Instance**
   - Ubuntu Server 22.04 LTS
   - t3.medium or larger (for better performance)
   - Open port 8501 in Security Group

2. **SSH into instance**:
```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
```

3. **Install Dependencies**:
```bash
sudo apt update
sudo apt install -y python3-pip git
```

4. **Clone and Setup**:
```bash
git clone https://github.com/YOUR_USERNAME/voc-portal.git
cd voc-portal
pip3 install -r requirements.txt
```

5. **Run with PM2 (keeps app running)**:
```bash
# Install PM2
sudo npm install -g pm2

# Start app
pm2 start "streamlit run app.py" --name voc-portal

# Auto-start on reboot
pm2 startup
pm2 save
```

6. **Setup Nginx Reverse Proxy** (optional, for custom domain):
```bash
sudo apt install nginx
sudo nano /etc/nginx/sites-available/voc-portal
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/voc-portal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Access**: `http://YOUR_EC2_IP:8501` or `http://your-domain.com`

---

### Option 5: Local Network Deployment

**Best for**: Internal team access, local organization

**Steps**:

1. **Find your local IP**:
```bash
# Windows
ipconfig
# Look for "IPv4 Address" (e.g., 192.168.1.100)

# Linux/Mac
ifconfig | grep "inet "
```

2. **Run Streamlit with network access**:
```bash
streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

3. **Share the URL**: `http://YOUR_LOCAL_IP:8501`
   - Example: `http://192.168.1.100:8501`
   - Anyone on your network can access it

4. **Open Firewall Port** (if needed):
```bash
# Windows Firewall
netsh advfirewall firewall add rule name="Streamlit" dir=in action=allow protocol=TCP localport=8501

# Linux (ufw)
sudo ufw allow 8501
```

---

### Security Considerations

For public deployments:

1. **Add Authentication** (Streamlit doesn't have built-in auth):

Create `auth.py`:
```python
import streamlit as st
import hashlib

def check_password():
    """Returns True if user entered correct password"""

    def password_entered():
        if hashlib.sha256(st.session_state["password"].encode()).hexdigest() == "YOUR_HASHED_PASSWORD":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("Password incorrect")
        return False
    else:
        return True
```

Add to `app.py`:
```python
from auth import check_password

if not check_password():
    st.stop()

# Rest of your app...
```

2. **Use HTTPS**: Enable SSL/TLS for secure connections
3. **Environment Variables**: Store sensitive data in `.env` files (not in git)
4. **Rate Limiting**: Prevent abuse with request limits

---

### Deployment Comparison

| Option | Cost | Ease | Performance | Control | Best For |
|--------|------|------|-------------|---------|----------|
| **Streamlit Cloud** | Free | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Demos, sharing |
| **Docker** | Varies | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Any platform |
| **Heroku** | $7+/mo | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Quick deploy |
| **AWS EC2** | $10+/mo | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Production |
| **Local Network** | Free | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Internal use |

---

### Quick Start: Streamlit Cloud (5 Minutes)

**Fastest way to share your portal**:

```bash
# 1. Initialize git (if not already)
git init
git add .
git commit -m "VOC Portal"

# 2. Push to GitHub (create repo first on github.com)
git remote add origin https://github.com/YOUR_USERNAME/voc-portal.git
git push -u origin main

# 3. Deploy on share.streamlit.io
# - Sign in with GitHub
# - Click "New app"
# - Select your repo
# - Deploy!

# Done! Share your URL: https://YOUR_USERNAME-voc-portal.streamlit.app
```

---

## Credits

Built with:
- [Streamlit](https://streamlit.io/) - Web application framework
- [Plotly](https://plotly.com/) - Interactive visualization
- [GeoPandas](https://geopandas.org/) - Geospatial data processing
- [PyKrige](https://github.com/GeoStat-Framework/PyKrige) - Kriging interpolation
- [SciPy](https://scipy.org/) - Scientific computing

## License

MIT License - Feel free to use and modify for your research and applications.

## Contact

For questions or issues, please refer to the documentation or create an issue in the project repository.
