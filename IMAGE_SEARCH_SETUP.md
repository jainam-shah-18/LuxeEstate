# Image Search Feature Setup Guide

## Problem
The "Search by Image" feature requires Nvidia NIM API access to analyze photos and detect property features (pool, kitchen, amenities, etc.).

## Solution: Get Your Nvidia NIM API Key

### Step 1: Sign Up at Nvidia
1. Go to [https://build.nvidia.com](https://build.nvidia.com)
2. Sign up or log in with your account
3. Agree to the terms

### Step 2: Generate an API Key
1. Click on your profile icon (top-right)
2. Select "API keys" or go to the API keys section
3. Click "Create new secret key"
4. Copy the key (it starts with `nvapi-`)
5. **Save it somewhere safe** – you won't be able to see it again!

### Step 3: Add to Your Project
1. Open the `.env` file in `c:\Indianic\LuxeEstate\LuxeEstate_updated\.env`
2. Add this line (replace with your actual API key):
   ```
   NVIDIA_API_KEY=nvapi-your-actual-api-key-here
   ```

### Step 4: Verify Configuration
1. Save the `.env` file
2. Restart the Django server:
   ```powershell
   cd c:\Indianic\LuxeEstate\LuxeEstate_updated
   .\venv\Scripts\Activate.ps1
   python manage.py runserver
   ```

### Step 5: Test the Feature
1. Upload a clear photo of a property room or outdoor area
2. Click "Search by Image"
3. You should see detected features and matching properties

## Troubleshooting

### Error: "Image search feature is not properly configured"
- **Cause**: NVIDIA_API_KEY is not set in `.env`
- **Fix**: Follow steps 1-4 above

### Error: "Invalid Nvidia NIM API key"
- **Cause**: API key is incorrect or has been revoked
- **Fix**: 
  1. Go to [https://build.nvidia.com](https://build.nvidia.com/api/keys)
  2. Verify your key is valid and active
  3. Generate a new key if needed

### Error: "Our AI could not detect recognisable property features"
- **Cause**: Photo is too blurry, too dark, or doesn't show property features
- **Fix**: Try uploading a clearer photo of:
  - A specific room (bedroom, kitchen, living room)
  - Outdoor area (garden, pool, terrace)
  - Architectural features

## Cost Considerations
- Nvidia NIM charges per API call (Llama models are free or low cost)
- Consider setting API usage limits in your Nvidia account dashboard

## Features Detected
The AI analyzes images for:
- **Outdoor**: Pool, terrace, garden, driveway, solar panels
- **Kitchen**: Modular, open-plan, island, pantry
- **Living**: Fireplace, high ceiling, floor-to-ceiling windows
- **Bedroom**: Walk-in wardrobe, en-suite bathroom
- **Bathroom**: Bathtub, rain shower, steam room
- **Building**: Villa, apartment, penthouse type
- **Amenities**: Gym, parking, security, lift, etc.

## More Info
- [Nvidia NIM API Documentation](https://docs.api.nvidia.com/nim/)
- [Nvidia Build Guide](https://build.nvidia.com)
