# How to Push to GitHub - Step by Step

## Step 1: Create a Personal Access Token

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a name: `AI_Summarize_Push`
4. Select expiration: Choose how long (30 days, 90 days, or no expiration)
5. **Check the `repo` checkbox** (this gives full repository access)
6. Scroll down and click **"Generate token"**
7. **COPY THE TOKEN IMMEDIATELY** (you won't see it again!)
   - It looks like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Step 2: Push Your Code

Open terminal and run:

```bash
cd /Users/peemmawat/AI_SUMMARIZE
git push -u origin main
```

When prompted:
- **Username:** `Peemmawat4508`
- **Password:** Paste your personal access token (the `ghp_...` token you copied)

That's it! Your code will be pushed to GitHub.

---

## Alternative: Use GitHub Desktop

If you prefer a GUI:
1. Download GitHub Desktop: https://desktop.github.com/
2. Sign in with your GitHub account
3. File → Add Local Repository → Select `/Users/peemmawat/AI_SUMMARIZE`
4. Click "Publish repository"
5. Done!

---

## Troubleshooting

**"Authentication failed"**
- Make sure you're using the token, not your GitHub password
- Check that the token has `repo` permissions

**"Repository not found"**
- Make sure the repository exists at: https://github.com/Peemmawat4508/AI_Summarize

