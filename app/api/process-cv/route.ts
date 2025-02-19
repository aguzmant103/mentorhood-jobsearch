import { writeFile, mkdir, readFile } from 'fs/promises';
import { NextRequest, NextResponse } from 'next/server';
import path from 'path';
import { spawn } from 'child_process';

// Helper function to execute Python script
async function runPythonScript(cvPath: string): Promise<{ csvPath: string, error?: string }> {
  return new Promise((resolve) => {
    const pythonProcess = spawn('python3', [
      path.join(process.cwd(), 'backend', 'job-search.py'),
      '--cv', cvPath
    ]);

    let outputData = '';
    let errorData = '';

    pythonProcess.stdout.on('data', (data) => {
      console.log('Python output:', data.toString());
      outputData += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error('Python error:', data.toString());
      errorData += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        resolve({ csvPath: '', error: errorData || 'Python script execution failed' });
        return;
      }
      resolve({ csvPath: path.join(process.cwd(), 'backend', 'jobs.csv') });
    });
  });
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;
    
    if (!file) {
      return NextResponse.json(
        { error: 'No file provided' },
        { status: 400 }
      );
    }

    // Ensure directories exist
    const backendDir = path.join(process.cwd(), 'backend');
    const uploadsDir = path.join(process.cwd(), 'public', 'uploads');
    await mkdir(backendDir, { recursive: true });
    await mkdir(uploadsDir, { recursive: true });

    // Save CV
    const cvPath = path.join(backendDir, 'cv.pdf');
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    await writeFile(cvPath, buffer);

    // Run Python script
    const { csvPath, error } = await runPythonScript(cvPath);
    
    if (error) {
      console.error('Python script error:', error);
      return NextResponse.json(
        { error: 'Job search process failed' },
        { status: 500 }
      );
    }

    try {
      // Copy CSV to public directory for download
      const publicCsvPath = path.join(process.cwd(), 'public', 'uploads', 'results.csv');
      const csvContent = await readFile(csvPath, 'utf-8');
      await writeFile(publicCsvPath, csvContent);
    } catch (error) {
      console.error('Error reading CSV:', error);
      return NextResponse.json(
        { error: 'Failed to read results' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      csvUrl: '/uploads/results.csv',
      message: 'CV processed successfully'
    });
  } catch (error) {
    console.error('API error:', error);
    return NextResponse.json(
      { error: 'Processing failed' },
      { status: 500 }
    );
  }
} 