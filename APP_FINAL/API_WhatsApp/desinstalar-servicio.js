
const { Service } = require('node-windows');
const path = require('path');

const svc = new Service({
    name: 'API Whatsapp SP',
    script: path.join(__dirname, 'app.js')
});

svc.on('uninstall', () => {
    console.log('✅ Servicio desinstalado correctamente');
});

svc.on('error', (err) => {
    console.error('❌ Error al desinstalar:', err);
});

svc.uninstall();