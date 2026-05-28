const {Service} = require('node-windows');
const path = require('path');


const svc = new Service({
    name: 'API Whatsapp SP',
    description: 'Servicio para ejecutar la API de WhatsApp del Sistema SP',
    script: path.join(__dirname, 'app.js'),
    workingDirectory: __dirname,
    // SIN logOnAs → corre como LocalSystem (no necesita contraseña)
    nodeOptions: [],
    // Reinicia automáticamente si crashea
    wait: 2,
    grow: 0.5,
    maxRestarts: 5
});



svc.on('install', () => {
    console.log('✅ Servicio instalado, iniciando...');
    svc.start();
});
svc.on('alreadyInstalled', () => {
    console.log('ℹ️ Servicio ya estaba instalado, iniciándolo...');
    svc.start();
});
svc.on('start', () => {
    console.log('🚀 Servicio iniciado correctamente');
});
svc.on('error', (err) => {
    console.error('❌ Error:', err);
});
svc.install();