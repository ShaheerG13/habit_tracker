let habitData = {};
let habitNames = {};
let currentHabitId = null;
let currentView = 1;
let currentDate = new Date();

function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function initializeSampleData() {
    habitNames = {
        1: "Morning Exercise",
        2: "Read 30 Minutes",
        3: "Meditation"
    };

    habitData = {1: {}, 2: {}, 3: {}};
    const today = new Date();
    
    for (let i = 90; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        const dateStr = formatDate(date);
        
        habitData[1][dateStr] = Math.random() > 0.3;
        habitData[2][dateStr] = Math.random() > 0.4;
        habitData[3][dateStr] = Math.random() > 0.5;
    }

    populateHabitSelector();
}

function populateHabitSelector() {
    const select = document.getElementById('habitSelect');
    select.innerHTML = '<option value="">Select a habit...</option>';
    
    for (const [id, name] of Object.entries(habitNames)) {
        const option = document.createElement('option');
        option.value = id;
        option.textContent = name;
        select.appendChild(option);
    }
}

function getMonthName(date) {
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
}

function getDaysInMonth(year, month) {
    return new Date(year, month + 1, 0).getDate();
}

function getFirstDayOfMonth(year, month) {
    return new Date(year, month, 1).getDay();
}

function renderMonth(year, month) {
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);
    const monthDate = new Date(year, month);
    
    const container = document.createElement('div');
    container.className = 'month-container';
    
    const header = document.createElement('div');
    header.className = 'month-header';
    header.textContent = getMonthName(monthDate);
    container.appendChild(header);
    
    const weekdays = document.createElement('div');
    weekdays.className = 'weekdays';
    ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].forEach(day => {
        const weekday = document.createElement('div');
        weekday.className = 'weekday';
        weekday.textContent = day;
        weekdays.appendChild(weekday);
    });
    container.appendChild(weekdays);
    
    const days = document.createElement('div');
    days.className = 'days';
    
    for (let i = 0; i < firstDay; i++) {
        const emptyDay = document.createElement('div');
        emptyDay.className = 'day empty';
        days.appendChild(emptyDay);
    }
    
    const today = formatDate(new Date());
    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);
        const dateStr = formatDate(date);
        const dayEl = document.createElement('div');
        dayEl.className = 'day';
        dayEl.textContent = day;
        
        if (dateStr === today) {
            dayEl.classList.add('today');
        }
        
        if (currentHabitId && habitData[currentHabitId]) {
            const completed = habitData[currentHabitId][dateStr];
            if (completed === true) {
                dayEl.classList.add('completed');
            } else if (completed === false) {
                dayEl.classList.add('incomplete');
            } else {
                dayEl.classList.add('neutral');
            }
        } else {
            dayEl.classList.add('neutral');
        }
        
        days.appendChild(dayEl);
    }
    
    container.appendChild(days);
    return container;
}

function renderCalendar() {
    const grid = document.getElementById('calendarGrid');
    grid.innerHTML = '';
    
    if (!currentHabitId) {
        grid.innerHTML = '<p style="text-align: center; color: #666; padding: 40px;">Please select a habit to view the calendar</p>';
        return;
    }
    
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    for (let i = 0; i < currentView; i++) {
        const displayDate = new Date(year, month + i);
        const monthContainer = renderMonth(displayDate.getFullYear(), displayDate.getMonth());
        grid.appendChild(monthContainer);
    }
    
    updatePeriodLabel();
}

function updatePeriodLabel() {
    const label = document.getElementById('currentPeriod');
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    if (currentView === 1) {
        label.textContent = getMonthName(currentDate);
    } else if (currentView === 3) {
        const endDate = new Date(year, month + 2);
        label.textContent = `${getMonthName(currentDate)} - ${getMonthName(endDate)}`;
    } else {
        label.textContent = year.toString();
    }
}

document.getElementById('habitSelect').addEventListener('change', (e) => {
    currentHabitId = e.target.value ? parseInt(e.target.value) : null;
    renderCalendar();
});

document.querySelectorAll('.view-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentView = parseInt(btn.dataset.view);
        
        const grid = document.getElementById('calendarGrid');
        grid.className = `calendar-grid view-${currentView}`;
        
        renderCalendar();
    });
});

document.getElementById('prevBtn').addEventListener('click', () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    if (currentView === 12) {
        currentDate = new Date(year - 1, 0);
    } else {
        currentDate = new Date(year, month - currentView);
    }
    
    renderCalendar();
});

document.getElementById('nextBtn').addEventListener('click', () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    if (currentView === 12) {
        currentDate = new Date(year + 1, 0);
    } else {
        currentDate = new Date(year, month + currentView);
    }
    
    renderCalendar();
});

function loadDataFromDatabase(habits, habitRows) {
    habitData = {};
    habitNames = {};
    
    habits.forEach(([id, name]) => {
        habitNames[id] = name;
        habitData[id] = {};
    });
    
    habitRows.forEach(([habitId, date, completed]) => {
        const dateStr = date instanceof Date ? formatDate(date) : date;
        habitData[habitId][dateStr] = completed;
    });
    
    populateHabitSelector();
    renderCalendar();
}

async function fetchHabitData() {
    try {
        const response = await fetch('/api/habit-data');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            console.error('API Error:', data.error);
            initializeSampleData();
            renderCalendar();
            return;
        }
        
        if (data.habits && data.habits.length > 0) {
            loadDataFromDatabase(data.habits, data.habitRows);
        } else {
            console.log('No habits found, showing sample data');
            initializeSampleData();
            renderCalendar();
        }
    } catch (error) {
        console.error('Error fetching habit data:', error);
        initializeSampleData();
        renderCalendar();
    }
}

fetchHabitData();