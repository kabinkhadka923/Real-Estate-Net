/**
 * Profile Dropdown Functionality for Real Estate Net
 */

/**
 * Show account settings - currently shows a placeholder message
 * TODO: Implement full account settings modal/page
 */
function showAccountSettings() {
    // For now, show an alert - can be improved to show a modal or redirect
    alert('Account settings feature is coming soon!\n\nFor now, you can update your profile in the Dashboard.');
}

// Initialize brand colors (fallback for CSS variables)
function initBrandColors() {
    // Ensure brand colors are applied even if CSS variables fail
    document.documentElement.style.setProperty('--nepal-blue', '#0033A0');
    document.documentElement.style.setProperty('--nepal-crimson', '#DC143C');
}

// Initialize map when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize brand colors
    initBrandColors();

    // Initialize map only if map element exists
    const mapElement = document.getElementById('map');
    if (mapElement) {
        try {
            initializeMap();
        } catch (error) {
            console.error('Error initializing map:', error);
        }
    }

    // Initialize property carousel if it exists
    const carousel = document.querySelector('.carousel');
    if (carousel) {
        try {
            initializeCarousel();
        } catch (error) {
            console.error('Error initializing carousel:', error);
        }
    }

    // Add mobile touch support for dropdown
    if (window.innerWidth <= 768) {
        const profileDropdown = document.querySelector('.profile-dropdown');

        if (profileDropdown) {
            profileDropdown.addEventListener('click', function() {
                const dropdown = this.querySelector('.dropdown-content');
                if (dropdown) {
                    dropdown.classList.toggle('show-mobile');
                }
            });
        }
    }
});

// Initialize Leaflet map
function initializeMap() {
    // Default center point (Kathmandu, Nepal)
    const defaultCenter = [27.7172, 85.3240];

    // Create map instance
    const map = L.map('map').setView(defaultCenter, 12);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18
    }).addTo(map);

    // Add sample property markers (replace with dynamic data from Django)
    addPropertyMarkers(map);

    // Add search functionality to map
    addMapSearch(map);
}

// Add property markers to map
function addPropertyMarkers(map) {
    // Sample property data - replace with actual data from Django backend
    const properties = [
        {
            id: 1,
            title: 'Modern Office Space',
            location: 'Kathmandu',
            lat: 27.7172,
            lng: 85.3240,
            price: 'NPR 50,000/month',
            type: 'Office',
            image: '/static/images/default-property.jpg'
        },
        {
            id: 2,
            title: 'Retail Space in Thamel',
            location: 'Thamel, Kathmandu',
            lat: 27.7150,
            lng: 85.3100,
            price: 'NPR 75,000/month',
            type: 'Retail',
            image: '/static/images/default-property.jpg'
        },
        {
            id: 3,
            title: 'Industrial Warehouse',
            location: 'Patan, Lalitpur',
            lat: 27.6730,
            lng: 85.3250,
            price: 'NPR 200,000/month',
            type: 'Industrial',
            image: '/static/images/default-property.jpg'
        }
    ];

    properties.forEach(property => {
        const marker = L.marker([property.lat, property.lng]).addTo(map);

        const popupContent = `
            <div class="map-popup">
                <img src="${property.image}" alt="${property.title}" style="width: 100%; height: 120px; object-fit: cover; border-radius: 5px; margin-bottom: 10px;">
                <h4 style="margin: 0 0 5px 0; color: #003893;">${property.title}</h4>
                <p style="margin: 0 0 5px 0; color: #666;">${property.location}</p>
                <p style="margin: 0 0 5px 0; color: #DC143C; font-weight: bold;">${property.price}</p>
                <p style="margin: 0 0 10px 0; color: #666;">Type: ${property.type}</p>
                <a href="/properties/${property.id}/" style="background-color: #003893; color: white; padding: 5px 10px; border-radius: 3px; text-decoration: none; font-size: 12px;">View Details</a>
            </div>
        `;

        marker.bindPopup(popupContent);
    });
}

// Add search functionality to map
function addMapSearch(map) {
    // Create a search control
    const searchControl = L.Control.extend({
        options: {
            position: 'topleft'
        },

        onAdd: function(map) {
            const container = L.DomUtil.create('div', 'leaflet-control-search');
            container.innerHTML = `
                <div style="background: white; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                    <input type="text" id="map-search" placeholder="Search location..." style="width: 200px; padding: 5px; border: 1px solid #ccc; border-radius: 3px;">
                </div>
            `;

            // Prevent map click when clicking on search control
            L.DomEvent.disableClickPropagation(container);

            return container;
        }
    });

    map.addControl(new searchControl());

    // Add search functionality
    document.getElementById('map-search').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const query = this.value;
            if (query) {
                searchLocation(map, query);
            }
        }
    });
}

// Search for location and center map
function searchLocation(map, query) {
    // Use Nominatim API for geocoding (OpenStreetMap)
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}, Nepal`)
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                const result = data[0];
                const lat = parseFloat(result.lat);
                const lng = parseFloat(result.lon);

                map.setView([lat, lng], 15);

                // Add a temporary marker for the searched location
                L.marker([lat, lng])
                    .addTo(map)
                    .bindPopup(`<b>${result.display_name}</b>`)
                    .openPopup();
            } else {
                alert('Location not found. Please try a different search term.');
            }
        })
        .catch(error => {
            console.error('Error searching location:', error);
            alert('Error searching location. Please try again.');
        });
}

// Initialize property carousel
function initializeCarousel() {
    const carousel = document.querySelector('.carousel');
    let isDown = false;
    let startX;
    let scrollLeft;

    carousel.addEventListener('mousedown', (e) => {
        isDown = true;
        carousel.classList.add('active');
        startX = e.pageX - carousel.offsetLeft;
        scrollLeft = carousel.scrollLeft;
    });

    carousel.addEventListener('mouseleave', () => {
        isDown = false;
        carousel.classList.remove('active');
    });

    carousel.addEventListener('mouseup', () => {
        isDown = false;
        carousel.classList.remove('active');
    });

    carousel.addEventListener('mousemove', (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - carousel.offsetLeft;
        const walk = (x - startX) * 2;
        carousel.scrollLeft = scrollLeft - walk;
    });

    // Touch support for mobile
    carousel.addEventListener('touchstart', (e) => {
        isDown = true;
        startX = e.touches[0].pageX - carousel.offsetLeft;
        scrollLeft = carousel.scrollLeft;
    });

    carousel.addEventListener('touchend', () => {
        isDown = false;
    });

    carousel.addEventListener('touchmove', (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.touches[0].pageX - carousel.offsetLeft;
        const walk = (x - startX) * 2;
        carousel.scrollLeft = scrollLeft - walk;
    });
}

/**
 * FUNNY INTERACTIVE LOGIN ANIMATIONS FOR REAL ESTATE NET
 */

let partyMode = false;
let clickCount = 0;
let floatingEmojis = [];

// Function to trigger party effects
function partyTime() {
    if (partyMode) return;

    partyMode = true;
    clickCount++;

    const card = document.querySelector('.login-card');
    const h1 = document.querySelector('.login-header h1');
    const emoji = document.querySelector('.welcome-emoji');
    const funnyText = document.getElementById('funny-text');

    // Add party effects
    card.style.animation = 'party 1s ease-in-out infinite';
    h1.style.animation = 'rainbow 0.5s linear infinite, shake 0.5s ease-out';
    emoji.style.animation = 'magic 1s ease-out infinite';

    // Create floating emojis
    for (let i = 0; i < 10; i++) {
        setTimeout(() => {
            createFloatingEmoji(['🎉', '🎈', '✨', '🏠', '🏡', '🚀', '💎'][Math.floor(Math.random() * 7)]);
        }, i * 200);
    }

    // Funny text updates with party themes
    const texts = [
        '🎉 PARTY TIME! LET\'S LOGIN! 🎉',
        '🏠 REAL ESTATE EXTRAVAGANZA! 🏠',
        '✨ MAGICAL LOGIN TIME! ✨',
        '🚀 ZOOMING INTO PROPERTIES! 🚀',
        '💎 DIAMOND-LEVEL AUTHENTICATION! 💎'
    ];
    if (funnyText) {
        funnyText.innerHTML = texts[clickCount % texts.length];
        funnyText.style.color = '#ff6b6b';
        funnyText.style.fontWeight = 'bold';
        funnyText.style.animation = 'heartbeat 0.5s ease-out';
    }

    // Play party sounds (simulated with alerts since we can't play real sounds)
    playPartyEffect();

    // Reset after 3 seconds
    setTimeout(() => {
        partyMode = false;
        card.style.animation = 'slideInFromLeft 1s ease-out 0.6s forwards, wiggle 2s ease-in-out 1.5s infinite';
        h1.style.animation = 'bounceIn 0.8s ease-out 1s both, rainbow 3s linear infinite 1.5s';
        emoji.style.animation = 'wave 2s ease-in-out infinite, bounceIn 0.8s ease-out 0.5s both';
        if (funnyText) {
            funnyText.style.color = '#ff6b6b';
            funnyText.innerHTML = 'Click me for another surprise! ✨';
        }
    }, 3500);
}

// Function to create floating emojis
function createFloatingEmoji(emoji) {
    if (floatingEmojis.length > 20) return; // Limit emoji count

    const emojiElement = document.createElement('div');
    emojiElement.textContent = emoji;
    emojiElement.style.position = 'fixed';
    emojiElement.style.fontSize = Math.random() * 30 + 20 + 'px';
    emojiElement.style.left = Math.random() * window.innerWidth + 'px';
    emojiElement.style.top = window.innerHeight + 'px';
    emojiElement.style.zIndex = '9999';
    emojiElement.style.pointerEvents = 'none';
    emojiElement.style.animation = 'floatUp 3s ease-out forwards';

    document.body.appendChild(emojiElement);
    floatingEmojis.push(emojiElement);

    // Remove emoji after animation
    setTimeout(() => {
        document.body.removeChild(emojiElement);
        floatingEmojis = floatingEmojis.filter(e => e !== emojiElement);
    }, 3000);
}

// Add floatUp animation to document head
document.head.insertAdjacentHTML('beforeend', '<style>@keyframes floatUp { from { transform: translateY(0) rotate(0deg); opacity: 1; } to { transform: translateY(-200px) rotate(360deg); opacity: 0; } }</style>');

// Function to play party effect (visual feedback)
function playPartyEffect() {
    // Create explosion effect around the card
    const card = document.querySelector('.login-card');
    for (let i = 0; i < 15; i++) {
        setTimeout(() => {
            const sparkle = document.createElement('div');
            sparkle.textContent = '⭐';
            sparkle.style.position = 'fixed';
            sparkle.style.left = card.offsetLeft + Math.random() * card.offsetWidth + 'px';
            sparkle.style.top = card.offsetTop + Math.random() * card.offsetHeight + 'px';
            sparkle.style.fontSize = '20px';
            sparkle.style.animation = 'explode 0.8s ease-out forwards';
            sparkle.style.zIndex = '9999';
            sparkle.style.pointerEvents = 'none';
            document.body.appendChild(sparkle);

            setTimeout(() => {
                document.body.removeChild(sparkle);
            }, 800);
        }, i * 50);
    }
}

// Function to handle emoji clicks
function playSound(type) {
    const emoji = document.querySelector('.welcome-emoji');
    emoji.style.animation = 'magic 0.8s ease-out';

    // Show different reactions based on type
    const reactions = {
        'hello': ['🖐️', '✋', '👏'],
        'wave': ['🌊', '🏄', '⛱️']
    };

    if (reactions[type]) {
        const reaction = reactions[type][Math.floor(Math.random() * reactions[type].length)];
        createFloatingEmoji(reaction);
    }

    // Add wiggle effect to card
    const card = document.querySelector('.login-card');
    card.style.animation = 'wiggle 1s ease-in-out';

    setTimeout(() => {
        card.style.animation = 'slideInFromLeft 1s ease-out 0.6s forwards, wiggle 2s ease-in-out 1.5s infinite';
        emoji.style.animation = 'wave 2s ease-in-out infinite, bounceIn 0.8s ease-out 0.5s both';
    }, 1000);
}

// Add click handler to funny text
document.addEventListener('DOMContentLoaded', function() {
    const funnyText = document.getElementById('funny-text');
    if (funnyText) {
        funnyText.addEventListener('click', function() {
            const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#dda0dd'];
            this.style.color = colors[Math.floor(Math.random() * colors.length)];
            this.style.animation = 'heartbeat 0.3s ease-out';

            const messages = [
                '🎈 BOING! Nice click! 🎈',
                '🏠 This house is magical! 🏠',
                '✨ You found the magic text! ✨',
                '🚀 To infinity and real estate! 🚀',
                '💎 Another click, another sparkle! 💎'
            ];
            this.innerHTML = messages[Math.floor(Math.random() * messages.length)];

            createFloatingEmoji('💫');
        });
    }

    // Add hover effects to form inputs
    const inputs = document.querySelectorAll('input[type="email"], input[type="password"]');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.style.animation = 'bounceIn 0.3s ease-out, wiggle 0.5s ease-in-out 0.3s';
            createFloatingEmoji('⭐');
        });

        input.addEventListener('blur', function() {
            this.style.animation = '';
        });
    });

    // Add special effect to submit button
    const submitBtn = document.querySelector('.login-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function() {
            this.style.animation = 'heartbeat 0.5s ease-out';
            this.innerHTML = '✨ MAGICAL LOGIN ✨';

            setTimeout(() => {
                this.innerHTML = '🔑 Sign In';
            }, 1000);
        });
    }

    // Signup page interactive elements
    const signupWelcomeEmoji = document.querySelector('.signup-header .welcome-emoji');
    if (signupWelcomeEmoji) {
        signupWelcomeEmoji.addEventListener('click', function() {
            const emojis = ['🎉', '🚀', '🏠', '💎', '✨', '🎈'];
            const randomEmoji = emojis[Math.floor(Math.random() * emojis.length)];
            createFloatingEmoji(randomEmoji);
            this.style.animation = 'magic 0.8s ease-out, bounceIn 0.5s ease-out';
        });
    }

    const signupFunnyText = document.getElementById('signup-funny-text');
    if (signupFunnyText) {
        let signupClickCount = 0;
        signupFunnyText.addEventListener('click', function() {
            signupClickCount++;
            const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7', '#dda0dd'];
            this.style.color = colors[signupClickCount % colors.length];
            this.style.animation = 'heartbeat 0.3s ease-out';

            const messages = [
                '🎈 SIGNUP CELEBRATION! 🎈',
                '🏠 WELCOME HOME! 🏠',
                '✨ MAGICAL MEMBERSHIP! ✨',
                '🚀 JOIN THE ROCKETSHIP! 🚀',
                '💎 DIAMOND MEMBER STATUS! 💎',
                '🎉 PARTY TIME REGISTRATION! 🎉'
            ];
            this.innerHTML = messages[signupClickCount % messages.length];

            // Special double-click effect
            signupFunnyText.addEventListener('dblclick', function() {
                // Trigger mega party
                for (let i = 0; i < 20; i++) {
                    setTimeout(() => {
                        createFloatingEmoji(['🎊', '🎇', '🎆', '🎉', '💥', '⭐'][Math.floor(Math.random() * 6)]);
                    }, i * 100);
                }

                const signupCard = document.querySelector('.signup-card');
                if (signupCard) {
                    signupCard.style.animation = 'party 2s ease-in-out infinite';
                    signupCard.style.transform = 'scale(1.05) rotate(1deg)';

                    const signupH1 = signupCard.querySelector('h1');
                    if (signupH1) {
                        signupH1.style.animation = 'rainbow 0.5s linear infinite, shake 0.5s ease-out';
                    }

                    setTimeout(() => {
                        signupCard.style.animation = 'slideInFromRight 0.8s ease-out 0.6s forwards';
                        signupCard.style.transform = '';
                        if (signupH1) {
                            signupH1.style.animation = 'bounceIn 0.8s ease-out 1s both, rainbow 3s linear infinite 1.5s';
                        }
                    }, 4000);
                }
            });
        });
    }
}

/**
 * SIGNUP PAGE FUNNY FUNCTIONS
 */

// Function for signup emoji greeting
function welcomeJoin() {
    const emoji = document.querySelector('.signup-header .welcome-emoji');
    emoji.style.animation = 'magic 0.8s ease-out';

    const reactions = ['🤝', '👏', '🙌', '🎯', '💪'];
    const reaction = reactions[Math.floor(Math.random() * reactions.length)];
    createFloatingEmoji(reaction);

    const signupCard = document.querySelector('.signup-card');
    if (signupCard) {
        signupCard.style.animation = 'wiggle 1s ease-in-out';
        setTimeout(() => {
            signupCard.style.animation = 'slideInFromRight 0.8s ease-out 0.6s forwards';
        }, 1000);
    }
}

// Function for signup party effects
function signupParty() {
    let signupPartyMode = false;

    if (signupPartyMode) return;

    signupPartyMode = true;
    let signupPartyClickCount = 0;
    signupPartyClickCount++;

    const signupCard = document.querySelector('.signup-card');
    const signupH1 = signupCard.querySelector('h1');
    const signupEmoji = document.querySelector('.signup-header .welcome-emoji');
    const signupFunnyText = document.getElementById('signup-funny-text');

    // Add signup party effects
    signupCard.style.animation = 'party 1s ease-in-out infinite';
    signupH1.style.animation = 'rainbow 0.5s linear infinite, shake 0.5s ease-out';
    signupEmoji.style.animation = 'magic 1s ease-out infinite';

    // Create floating emojis for signup
    for (let i = 0; i < 12; i++) {
        setTimeout(() => {
            createFloatingEmoji(['🎉', '🚀', '🏠', '💎', '📋', '✍️', '💼', '🏢'][Math.floor(Math.random() * 8)]);
        }, i * 150);
    }

    // Funny signup text updates
    const signupTexts = [
        '🎉 JOINING THE REAL ESTATE FAMILY! 🎉',
        '🏠 WELCOME TO YOUR PROPERTY FUTURE! 🏠',
        '✨ SIGNUP MAGIC STARTS NOW! ✨',
        '🚀 REGISTRATION ROCKET LAUNCH! 🚀',
        '💎 PRESTIGE MEMBER STATUS! 💎',
        '📋 VIP REAL ESTATE CLUB! 📋'
    ];
    if (signupFunnyText) {
        signupFunnyText.innerHTML = signupTexts[signupPartyClickCount % signupTexts.length];
        signupFunnyText.style.color = '#ff6b6b';
        signupFunnyText.style.fontWeight = 'bold';
        signupFunnyText.style.animation = 'heartbeat 0.5s ease-out';
    }

    // Create signup celebration sparkles
    playSignupPartyEffect();

    // Reset after 4 seconds
    setTimeout(() => {
        signupPartyMode = false;
        signupCard.style.animation = 'slideInFromRight 0.8s ease-out 0.6s forwards';
        signupH1.style.animation = 'bounceIn 0.8s ease-out 1s both, rainbow 3s linear infinite 1.5s';
        signupEmoji.style.animation = 'wave 2s ease-in-out infinite, bounceIn 0.8s ease-out 0.5s both';
        if (signupFunnyText) {
            signupFunnyText.style.color = '#ff6b6b';
            signupFunnyText.innerHTML = 'Click me for another signup celebration! ✨';
        }
    }, 4000);
}

// Signup party celebration function
function playSignupPartyEffect() {
    const signupCard = document.querySelector('.signup-card');
    for (let i = 0; i < 18; i++) {
        setTimeout(() => {
            const sparkle = document.createElement('div');
            sparkle.textContent = ['✨', '⭐', '💫', '🎯', '🏆'][Math.floor(Math.random() * 5)];
            sparkle.style.position = 'fixed';
            sparkle.style.left = signupCard.offsetLeft + Math.random() * signupCard.offsetWidth + 'px';
            sparkle.style.top = signupCard.offsetTop + Math.random() * signupCard.offsetHeight + 'px';
            sparkle.style.fontSize = '24px';
            sparkle.style.animation = 'explode 1s ease-out forwards';
            sparkle.style.zIndex = '9999';
            sparkle.style.pointerEvents = 'none';
            document.body.appendChild(sparkle);

            setTimeout(() => {
                document.body.removeChild(sparkle);
            }, 1000);
        }, i * 60);
    }
}
