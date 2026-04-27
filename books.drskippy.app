server {
    listen 83;
    server_name books.drskippy.app;

    root /var/www/html/personal-book-records/book-records-react/dist;
    index index.html;

    # Ollama reverse proxy — browser can't reach 192.168.1.90 directly
    location /ollama/ {
        proxy_pass http://192.168.1.91:1234/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }

    # SPA routing — all paths fall back to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Vite outputs content-hashed assets — cache aggressively
    location ~* \.(js|css|woff2?|ttf|eot|svg|png|jpg|jpeg|gif|ico|webp)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Cloudflare Zero Trust tunnel: cloudflared runs at 192.168.1.172 on this
    # network. CF-Connecting-IP carries the real client IP.
    real_ip_header CF-Connecting-IP;
    set_real_ip_from 192.168.1.172;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml text/javascript image/svg+xml;
    gzip_min_length 1000;
}
