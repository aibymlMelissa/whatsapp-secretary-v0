const { Client, LocalAuth } = require('whatsapp-web.js');

console.log('Starting simple WhatsApp test...');

const client = new Client({
    authStrategy: new LocalAuth({
        dataPath: './test-session'
    }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process',
            '--disable-gpu'
        ]
    }
});

client.on('qr', (qr) => {
    console.log('✅ QR Code received successfully!');
    console.log('QR Code data:', qr.substring(0, 50) + '...');
});

client.on('ready', () => {
    console.log('✅ WhatsApp Client is ready!');
    process.exit(0);
});

client.on('authenticated', () => {
    console.log('✅ WhatsApp authenticated');
});

client.on('auth_failure', (msg) => {
    console.error('❌ Authentication failed:', msg);
    process.exit(1);
});

client.on('disconnected', (reason) => {
    console.log('❌ WhatsApp disconnected:', reason);
    process.exit(1);
});

console.log('Initializing WhatsApp client...');
client.initialize().catch((error) => {
    console.error('❌ Failed to initialize:', error);
    process.exit(1);
});

// Set a timeout to prevent hanging
setTimeout(() => {
    console.log('❌ Timeout reached, exiting...');
    process.exit(1);
}, 30000); // 30 seconds timeout