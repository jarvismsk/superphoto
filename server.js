const express = require('express');
const multer = require('multer');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const morgan = require('morgan');
const cors = require('cors');
const helmet = require('helmet');

const app = express();
const port = process.env.PORT || 4000;

const UPLOAD_DIR = './uploads';

// Ensure upload directory exists
if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR);
}

// Middleware setup
app.use(cors());
app.use(helmet());
app.use(morgan('combined'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, UPLOAD_DIR);
  },
  filename: function (req, file, cb) {
    cb(null, Date.now() + '-' + file.originalname);
  }
});

const upload = multer({ storage: storage });

// Endpoint to process image
app.post('/upload', upload.single('image'), (req, res) => {
  const imagePath = req.file.path;
  const outputFileName = path.basename(req.file.originalname, path.extname(req.file.originalname)) + '_processed.png';
  const outputPath = path.join(UPLOAD_DIR, outputFileName);

  const pythonProcess = spawn('python3', ['process_passport_photo.py', imagePath, outputPath]);

  pythonProcess.stdout.on('data', (data) => {
    console.log(`stdout: ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`stderr: ${data}`);
  });

  pythonProcess.on('close', (code) => {
    if (code === 0) {
      if (fs.existsSync(outputPath)) {
        res.send({ success: true, output_path: outputPath });
      } else {
        res.status(500).send({ success: false, message: 'Processing completed, but output file not found.' });
      }
    } else {
      res.status(500).send({ success: false, message: 'Image processing failed.' });
    }
  });
});

app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send('Something broke!');
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
