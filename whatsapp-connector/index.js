// index.js
// Versi final menggunakan LocalAuth yang modern dan stabil

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

// URL API Python kamu
const PYTHON_API_URL = 'http://localhost:5000/chat';

console.log('Memulai inisialisasi client...');

const client = new Client({
    authStrategy: new LocalAuth(), // Menggunakan LocalAuth untuk menyimpan sesi secara otomatis
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

client.on('qr', (qr) => {
    console.log('====================================================');
    console.log('              SILAHKAN SCAN QR CODE INI');
    console.log('====================================================');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('🚀 Client siap dan terhubung ke WhatsApp! Bot sekarang ONLINE.');
});

client.on('auth_failure', msg => {
    console.error('❌ GAGAL AUTENTIKASI:', msg);
    console.error('Coba hapus folder .wwebjs_auth dan jalankan ulang.');
});

client.on('message', async (message) => {
    // Abaikan pesan dari grup atau status
    if (message.from.endsWith('@g.us') || message.isStatus) {
        return;
    }
    
    const senderId = message.from;
    const text = message.body;

    console.log(`📩 Pesan diterima dari ${senderId}: "${text}"`);

    if (!text || text.trim() === '') return;

      try {
        // Kirim pesan ke API Python untuk diproses
        console.log("🔄 Mengirim pesan ke API Python untuk diproses...");
        const response = await axios.post(PYTHON_API_URL, {
            user_id: senderId,
            message: text
        });

        const botReply = response.data.response;

        if (botReply) {
            console.log(`🤖 Balasan dari API Python: "${botReply}"`);

            // Tambahan debug: cek isi flow conversation
            if (botReply.toLowerCase().includes("posisi kamu") || botReply.toLowerCase().includes("fakultas")) {
                console.log("➡️ Flow: User lagi di fase **waiting_location**");
            } else if (botReply.toLowerCase().includes("tingkat kelaparan") || botReply.toLowerCase().includes("brutal")) {
                console.log("➡️ Flow: User lagi di fase **waiting_hunger**");
            } else if (botReply.toLowerCase().includes("budget") || botReply.toLowerCase().includes("berapa")) {
                console.log("➡️ Flow: User lagi di fase **waiting_budget**");
            } else if (botReply.toLowerCase().includes("opsi paling mantul")) {
                console.log("✅ Flow: Rekomendasi sudah dikirim ke user");
            }

            await client.sendMessage(senderId, botReply);
        } else {
            console.warn(`⚠️ Tidak ada balasan dari API Python untuk pesan: "${text}"`);
        }

    } catch (error) {
        console.error(`❌ Error saat menghubungi API Python: ${error.message}`);
        await client.sendMessage(senderId, 'Aduh, mamang lagi pusing nih, coba beberapa saat lagi ya! 😵');
    }
});

client.initialize();