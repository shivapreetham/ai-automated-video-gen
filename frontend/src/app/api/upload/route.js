import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { NextResponse } from 'next/server';

// Configure Cloudflare R2 client
const r2Client = new S3Client({
  region: 'auto',
  endpoint: `https://${process.env.CLOUDFLARE_R2_ACCOUNT_ID}.r2.cloudflarestorage.com`,
  credentials: {
    accessKeyId: process.env.CLOUDFLARE_R2_ACCESS_KEY_ID,
    secretAccessKey: process.env.CLOUDFLARE_R2_SECRET_ACCESS_KEY,
  },
});

export async function POST(request) {
  try {
    const formData = await request.formData();
    const file = formData.get('file');
    const fileName = formData.get('fileName') || `video-${Date.now()}.mp4`;

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    // Convert file to buffer
    const buffer = await file.arrayBuffer();
    const fileBuffer = Buffer.from(buffer);

    // Upload to Cloudflare R2
    const command = new PutObjectCommand({
      Bucket: process.env.CLOUDFLARE_R2_BUCKET_NAME,
      Key: fileName,
      Body: fileBuffer,
      ContentType: 'video/mp4',
      ContentDisposition: 'inline', // Allow viewing in browser
    });

    await r2Client.send(command);

    // Generate public URL
    const publicUrl = `${process.env.CLOUDFLARE_R2_PUBLIC_URL}/${fileName}`;

    return NextResponse.json({
      success: true,
      fileName: fileName,
      publicUrl: publicUrl,
      message: 'Video uploaded successfully'
    });

  } catch (error) {
    console.error('R2 Upload Error:', error);
    return NextResponse.json(
      { error: 'Upload failed', details: error.message },
      { status: 500 }
    );
  }
}