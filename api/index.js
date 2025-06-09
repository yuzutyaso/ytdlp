// api/index.js (or app.py if using Python)

const express = require('express');
const { exec } = require('child_process');
const path = require('path');
const fs = require('fs/promises'); // For async file operations

const app = express();
app.use(express.json());

// A temporary directory for downloads within the ephemeral Vercel environment.
// Note: Files stored here will be deleted after the function execution.
const DOWNLOAD_DIR = '/tmp'; 

// Helper function to execute shell commands
const executeCommand = (command) => {
    return new Promise((resolve, reject) => {
        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.error(`exec error: ${error}`);
                return reject(error);
            }
            if (stderr) {
                console.warn(`stderr: ${stderr}`);
            }
            resolve(stdout);
        });
    });
};

app.post('/convert', async (req, res) => {
    const { youtubeUrl } = req.body;

    if (!youtubeUrl) {
        return res.status(400).json({ error: 'YouTube URL is required.' });
    }

    // Basic URL validation (you might want a more robust one)
    if (!youtubeUrl.startsWith('https://www.youtube.com/watch?v=')) {
        return res.status(400).json({ error: 'Invalid YouTube URL format.' });
    }

    let filePath = '';
    try {
        // Generate a unique filename
        const videoId = new URL(youtubeUrl).searchParams.get('v');
        const filename = `${videoId}-${Date.now()}.webm`;
        filePath = path.join(DOWNLOAD_DIR, filename);

        // Command to download high-quality webm with audio
        // -f bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]
        // --merge-output-format webm
        // -o ensures the output filename
        // --no-part prevents creation of .part files which might cause issues in serverless
        // --quiet suppresses console output from yt-dlp itself
        const command = `yt-dlp -f "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]" --merge-output-format webm "${youtubeUrl}" -o "${filePath}" --no-part --quiet`;
        
        console.log(`Executing yt-dlp command: ${command}`);
        await executeCommand(command);

        // --- IMPORTANT CONSIDERATION FOR VERCEL ---
        // Vercel serverless functions have an ephemeral filesystem.
        // You cannot serve files directly from /tmp to the client in a persistent way.
        // You MUST upload the generated .webm file to a persistent storage service
        // (like AWS S3, Cloudinary, Google Cloud Storage) and return THAT URL.
        // For demonstration, we'll imagine a placeholder upload function.

        // Placeholder for file upload and getting a public URL
        const publicWebmUrl = `https://your-storage-service.com/videos/${filename}`; // Replace with actual upload logic

        // Example: If you wanted to send the file back directly (ONLY FOR SMALL FILES AND TESTING, NOT RECOMMENDED FOR PRODUCTION)
        // const fileBuffer = await fs.readFile(filePath);
        // return res.status(200).send(fileBuffer); // This would send the binary data

        res.status(200).json({
            message: 'Video converted successfully!',
            webmUrl: publicWebmUrl,
            // In a real scenario, you'd also include other metadata from yt-dlp if needed
        });

    } catch (error) {
        console.error('Conversion failed:', error);
        res.status(500).json({ error: 'Failed to convert video.', details: error.message });
    } finally {
        // Clean up the downloaded file (important for serverless to free up space)
        if (filePath) {
            try {
                await fs.unlink(filePath);
                console.log(`Cleaned up file: ${filePath}`);
            } catch (cleanupError) {
                console.warn(`Failed to clean up file ${filePath}:`, cleanupError);
            }
        }
    }
});

// For Vercel, export the app
module.exports = app;
