import { S3Client, DeleteObjectCommand } from '@aws-sdk/client-s3';
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

export async function DELETE(request) {
  try {
    const { searchParams } = new URL(request.url);
    const fileName = searchParams.get('fileName');

    if (!fileName) {
      return NextResponse.json({ error: 'File name is required' }, { status: 400 });
    }

    // Delete from Cloudflare R2
    const command = new DeleteObjectCommand({
      Bucket: process.env.CLOUDFLARE_R2_BUCKET_NAME,
      Key: fileName,
    });

    await r2Client.send(command);

    return NextResponse.json({
      success: true,
      message: 'Video deleted successfully',
      fileName: fileName
    });

  } catch (error) {
    console.error('R2 Delete Error:', error);
    return NextResponse.json(
      { error: 'Delete failed', details: error.message },
      { status: 500 }
    );
  }
}