-- 1. Insert Categories
-- Karena kategori didapat dari JSON, kita buat dulu kategorinya
insert into public.kategori (nama) values 
('Pengembangan Software & Web Dev'),
('Pengembangan Software & Toko Online'),
('Pengembangan Software & Mobile Dev'),
('Pengembangan Software & ERP/CRM'),
('Foto & Videografi Kreatif'),
('Event Digital Solution (Event Tech)'),
('Event Digital Solution & RFID Tech'),
('Paket Bundling Spesial');

-- 2. Insert Products (Ini butuh ID kategori yang dinamis, 
-- dalam SQL ini kita ambil ID dengan subquery berdasarkan nama kategori)
insert into public.produk (kategori_id, nama, harga, deskripsi, fitur, alur) values 
((select id from public.kategori where nama = 'Pengembangan Software & Web Dev'), 'Website Company Profile', 1500000, 'Layanan pembuatan website profesional...', '[]'::jsonb, '[]'::jsonb),
((select id from public.kategori where nama = 'Pengembangan Software & Toko Online'), 'Website E-Commerce', 5000000, 'Platform toko online...', '[]'::jsonb, '[]'::jsonb),
((select id from public.kategori where nama = 'Pengembangan Software & Mobile Dev'), 'Aplikasi Mobile iOS & Android', 4000000, 'Pengembangan aplikasi...', '[]'::jsonb, '[]'::jsonb),
((select id from public.kategori where nama = 'Pengembangan Software & ERP/CRM'), 'Dashboard Admin & API System', 2000000, 'Sistem manajemen data internal...', '[]'::jsonb, '[]'::jsonb),
((select id from public.kategori where nama = 'Foto & Videografi Kreatif'), 'Dokumentasi Event Organizer & Seminar', 350000, 'Layanan liputan...', '[]'::jsonb, '[]'::jsonb),
((select id from public.kategori where nama = 'Foto & Videografi Kreatif'), 'Pernikahan & Wisuda (Wedding & Graduation)', 150000, 'Abadikan momen...', '[]'::jsonb, '[]'::jsonb),
((select id from public.kategori where nama = 'Foto & Videografi Kreatif'), 'Running Event & Gathering Komunitas', 800000, 'Layanan dokumentasi khusus...', '[]'::jsonb, '[]'::jsonb),
((select id from public.kategori where nama = 'Foto & Videografi Kreatif'), 'Drone Photography & Aerial Videography', 1000000, 'Pengambilan visual...', '[]'::jsonb, '[]'::jsonb),
((select id from public.kategori where nama = 'Event Digital Solution (Event Tech)'), 'QR Code Check-in & E-Ticket System', 800000, 'Solusi manajemen registrasi...', '[]'::jsonb, '[]'::jsonb),
((select id from public.kategori where nama = 'Event Digital Solution (Event Tech)'), 'Live Participant Monitoring System', 500000, 'Dasbor pemantauan...', '[]'::jsonb, '[]'::jsonb),
((select id from public.kategori where nama = 'Event Digital Solution & RFID Tech'), 'Leaderboard & Timing System (RFID)', 500000, 'Sistem pencatatan waktu...', '[]'::jsonb, '[]'::jsonb),
((select id from public.kategori where nama = 'Event Digital Solution (Event Tech)'), 'Sertifikat Digital & Mass Blast', 500000, 'Layanan pembuatan...', '[]'::jsonb, '[]'::jsonb),
((select id from public.kategori where nama = 'Paket Bundling Spesial'), 'Paket Sport / Running Event All-in-One', 25000000, 'Solusi terintegrasi...', '[]'::jsonb, '[]'::jsonb),
((select id from public.kategori where nama = 'Paket Bundling Spesial'), 'Paket Corporate Seminar Pro', 15000000, 'Standar profesional...', '[]'::jsonb, '[]'::jsonb),
((select id from public.kategori where nama = 'Paket Bundling Spesial'), 'Paket Digital Wedding & Celebration', 12500000, 'Perpaduan sempurna...', '[]'::jsonb, '[]'::jsonb);
