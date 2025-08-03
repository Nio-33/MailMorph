document.addEventListener('DOMContentLoaded', function () {
    // --- Particle Animation --- //
    const canvas = document.getElementById('particle-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let width = (canvas.width = window.innerWidth);
        let height = (canvas.height = window.innerHeight);
        const particles = [];
        const particleCount = 60;
        const colors = ["#3B82F6", "#10B981", "#60A5FA", "#0EA5E9", "#8B5CF6"];

        class Particle {
            constructor() {
                this.x = Math.random() * width;
                this.y = Math.random() * height;
                this.size = Math.random() * 3 + 1;
                this.speedX = (Math.random() - 0.5) * 0.5;
                this.speedY = (Math.random() - 0.5) * 0.5;
                this.color = colors[Math.floor(Math.random() * colors.length)];
            }
            update() {
                this.x += this.speedX;
                this.y += this.speedY;
                if (this.x > width) this.x = 0;
                if (this.x < 0) this.x = width;
                if (this.y > height) this.y = 0;
                if (this.y < 0) this.y = height;
            }
            draw() {
                ctx.fillStyle = this.color;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        function initParticles() {
            for (let i = 0; i < particleCount; i++) {
                particles.push(new Particle());
            }
        }

        function animateParticles() {
            ctx.clearRect(0, 0, width, height);
            ctx.fillStyle = "#0F172A";
            ctx.fillRect(0, 0, width, height);
            particles.forEach((p) => {
                p.update();
                p.draw();
            });
            connectParticles();
            requestAnimationFrame(animateParticles);
        }

        function connectParticles() {
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    if (distance < 100) {
                        ctx.strokeStyle = `rgba(59, 130, 246, ${1 - distance / 120})`;
                        ctx.lineWidth = 0.5;
                        ctx.beginPath();
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.stroke();
                    }
                }
            }
        }

        window.addEventListener("resize", () => {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        });

        initParticles();
        animateParticles();
    }

    // --- Form Handling --- //
    const uploadForm = document.getElementById('uploadForm');
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('file');
    const filePreview = document.getElementById('filePreview');
    const oldDomainInput = document.getElementById('old_domain');
    const newDomainInput = document.getElementById('new_domain');

    if (dropZone) {
        dropZone.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', () => handleFiles(fileInput.files));

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
        });

        dropZone.addEventListener('drop', (e) => handleFiles(e.dataTransfer.files), false);
    }

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function handleFiles(files) {
        if (files.length === 0) return;
        const file = files[0];

        if (!isValidFile(file)) {
            filePreview.textContent = 'Invalid file. Please use CSV or TXT, under 16MB.';
            fileInput.value = '';
            return;
        }

        // Create a new DataTransfer object and add the file.
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;

        filePreview.textContent = `Selected: ${file.name}`;
    }

    function isValidFile(file) {
        const allowedTypes = ['text/csv', 'text/plain', 'application/vnd.ms-excel'];
        const extension = file.name.split('.').pop().toLowerCase();
        return (allowedTypes.includes(file.type) || ['csv', 'txt'].includes(extension)) && file.size <= 16 * 1024 * 1024;
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', function (e) {
            const isOldValid = validateDomain(oldDomainInput);
            const isNewValid = validateDomain(newDomainInput);

            if (!fileInput.files[0]) {
                alert('Please select a file.');
                e.preventDefault();
                return;
            }

            if (!isOldValid || !isNewValid || oldDomainInput.value.trim() === newDomainInput.value.trim()) {
                if(oldDomainInput.value.trim() === newDomainInput.value.trim()) {
                    setError(newDomainInput, 'Domains must be different.');
                }
                e.preventDefault();
                return;
            }
        });
    }

    [oldDomainInput, newDomainInput].forEach(input => {
        input.addEventListener('input', () => validateDomain(input));
    });

    function validateDomain(input) {
        const domainRegex = /^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (input.value.trim() === '' || !domainRegex.test(input.value.trim())) {
            setError(input, 'Please enter a valid domain.');
            return false;
        }
        clearError(input);
        return true;
    }

    function setError(input, message) {
        input.nextElementSibling.textContent = message;
    }

    function clearError(input) {
        input.nextElementSibling.textContent = '';
    }
});