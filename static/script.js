// Grand Azure Hotel - Management System JavaScript

document.addEventListener('DOMContentLoaded', function() {
  
    initDateInputs();
    initBookingCalculator();
    initFilterButtons();
    initFlashMessages();
});


function initDateInputs() {
    const today = new Date().toISOString().split('T')[0];
    const checkInInput = document.getElementById('check_in_date');
    const checkOutInput = document.getElementById('check_out_date');
    
    if (checkInInput) {
        checkInInput.setAttribute('min', today);
        checkInInput.addEventListener('change', function() {
            if (checkOutInput) {
                checkOutInput.setAttribute('min', this.value);
                if (checkOutInput.value && checkOutInput.value <= this.value) {
                    checkOutInput.value = '';
                }
            }
            updateBookingSummary();
        });
    }
    
    if (checkOutInput) {
        checkOutInput.setAttribute('min', today);
        checkOutInput.addEventListener('change', updateBookingSummary);
    }
}


function initBookingCalculator() {
    const roomSelect = document.getElementById('room_id');
    
    if (roomSelect) {
        roomSelect.addEventListener('change', updateBookingSummary);
    }
}

function updateBookingSummary() {
    const roomSelect = document.getElementById('room_id');
    const checkInInput = document.getElementById('check_in_date');
    const checkOutInput = document.getElementById('check_out_date');
    const summaryDiv = document.getElementById('booking-summary');
    
    if (!roomSelect || !checkInInput || !checkOutInput || !summaryDiv) return;
    
    const selectedOption = roomSelect.options[roomSelect.selectedIndex];
    const pricePerNight = parseFloat(selectedOption.dataset.price) || 0;
    const checkIn = new Date(checkInInput.value);
    const checkOut = new Date(checkOutInput.value);
    
    if (pricePerNight > 0 && checkInInput.value && checkOutInput.value && checkOut > checkIn) {
        const nights = Math.ceil((checkOut - checkIn) / (1000 * 60 * 60 * 24));
        const total = nights * pricePerNight;
        
        document.getElementById('nights-count').textContent = nights;
        document.getElementById('price-per-night').textContent = '$' + pricePerNight.toFixed(2);
        document.getElementById('total-amount').textContent = '$' + total.toFixed(2);
        
        summaryDiv.style.display = 'block';
    } else {
        summaryDiv.style.display = 'none';
    }
}


function initFilterButtons() {
    const filterBtns = document.querySelectorAll('.filter-btn');
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;
            
           
            filterBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            
            const roomCards = document.querySelectorAll('.room-card');
            const tableRows = document.querySelectorAll('tbody tr[data-status]');
            
            if (roomCards.length > 0) {
                roomCards.forEach(card => {
                    if (filter === 'all' || card.dataset.status === filter) {
                        card.style.display = '';
                    } else {
                        card.style.display = 'none';
                    }
                });
            }
            
            if (tableRows.length > 0) {
                tableRows.forEach(row => {
                    if (filter === 'all' || row.dataset.status === filter) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                });
            }
        });
    });
}


function initFlashMessages() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });
}


const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(20px);
        }
    }
`;
document.head.appendChild(style);

