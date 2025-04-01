document.addEventListener('DOMContentLoaded', function() {
    // Theme toggling
    const themeToggle = document.getElementById('themeToggle');
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Set initial theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    } else {
        document.documentElement.setAttribute('data-theme', 
            prefersDarkScheme.matches ? 'dark' : 'light');
    }
    
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
    
    // Handle mobile menu
    const mobileMenuBtn = document.createElement('button');
    mobileMenuBtn.className = 'mobile-menu-btn';
    mobileMenuBtn.innerHTML = '<i class="fas fa-bars"></i>';
    
    const navLinks = document.querySelector('.nav-links');
    const navContainer = document.querySelector('.nav-container');
    
    if (window.innerWidth <= 768) {
        navContainer.insertBefore(mobileMenuBtn, navLinks);
        navLinks.style.display = 'none';
    }
    
    mobileMenuBtn.addEventListener('click', () => {
        const isVisible = navLinks.style.display === 'flex';
        navLinks.style.display = isVisible ? 'none' : 'flex';
        mobileMenuBtn.innerHTML = isVisible ? 
            '<i class="fas fa-bars"></i>' : 
            '<i class="fas fa-times"></i>';
    });
    
    // Handle window resize
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            navLinks.style.display = 'flex';
            mobileMenuBtn.remove();
        } else {
            if (!document.querySelector('.mobile-menu-btn')) {
                navContainer.insertBefore(mobileMenuBtn, navLinks);
                navLinks.style.display = 'none';
            }
        }
    });
    
    // Handle alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
    
    // Handle user menu
    const userMenu = document.querySelector('.user-menu');
    if (userMenu) {
        const userMenuBtn = userMenu.querySelector('.user-menu-btn');
        const userDropdown = userMenu.querySelector('.user-dropdown');
        
        userMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.style.display = 
                userDropdown.style.display === 'block' ? 'none' : 'block';
        });
        
        document.addEventListener('click', () => {
            userDropdown.style.display = 'none';
        });
    }
    
    // Handle smooth scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Handle infinite scroll
    let isLoading = false;
    let currentPage = 1;
    
    function loadMoreContent() {
        if (isLoading) return;
        
        const loadMoreBtn = document.getElementById('loadMoreBtn');
        if (!loadMoreBtn) return;
        
        isLoading = true;
        loadMoreBtn.style.opacity = '0.5';
        
        fetch(`/api/articles?page=${currentPage + 1}`)
            .then(response => response.json())
            .then(data => {
                if (data.articles.length > 0) {
                    // Append new articles to the grid
                    const grid = document.querySelector('.discover-grid');
                    data.articles.forEach(article => {
                        // Create and append new article cards
                        // This would be implemented based on your article card template
                    });
                    currentPage++;
                } else {
                    loadMoreBtn.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error loading more articles:', error);
            })
            .finally(() => {
                isLoading = false;
                loadMoreBtn.style.opacity = '1';
            });
    }
    
    // Intersection Observer for infinite scroll
    const loadMoreObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                loadMoreContent();
            }
        });
    }, { threshold: 0.5 });
    
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (loadMoreBtn) {
        loadMoreObserver.observe(loadMoreBtn);
    }
    
    // Handle article interactions
    document.addEventListener('click', (e) => {
        // Bookmark functionality
        if (e.target.closest('.bookmark-btn')) {
            const btn = e.target.closest('.bookmark-btn');
            const articleUrl = btn.dataset.articleUrl;
            
            fetch('/api/bookmark', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ article_url: articleUrl })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    btn.classList.toggle('active');
                    const icon = btn.querySelector('i');
                    icon.classList.toggle('fas');
                    icon.classList.toggle('far');
                }
            })
            .catch(error => {
                console.error('Error bookmarking article:', error);
            });
        }
        
        // Share functionality
        if (e.target.closest('.share-btn')) {
            const btn = e.target.closest('.share-btn');
            const card = btn.closest('.article-card, .bookmark-card');
            const articleUrl = card.dataset.articleUrl;
            const title = card.querySelector('.article-title, .bookmark-title').textContent;
            
            if (navigator.share) {
                navigator.share({
                    title: title,
                    url: articleUrl
                })
                .catch(error => {
                    console.error('Error sharing:', error);
                    copyToClipboard(articleUrl, btn);
                });
            } else {
                copyToClipboard(articleUrl, btn);
            }
        }
    });
    
    // Helper function to copy to clipboard
    function copyToClipboard(text, btn) {
        navigator.clipboard.writeText(text)
            .then(() => {
                const originalContent = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(() => {
                    btn.innerHTML = originalContent;
                }, 2000);
            })
            .catch(error => {
                console.error('Error copying to clipboard:', error);
            });
    }
}); 