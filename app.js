// ===== BOARDS-AI Data Explorer (API Version) =====

// Configuration
const API_BASE = 'https://boardsai-api.ankush-rads.workers.dev';

// State
let caseIndex = [];
let filteredCases = [];
let currentCaseId = null;
let currentCaseData = null;
let currentView = 'mcq'; // 'mcq' or 'eval'
let selectedMcq = 1;

// Get access token from URL
const urlParams = new URLSearchParams(window.location.search);
const accessToken = urlParams.get('access');

// DOM Elements
const caseGrid = document.getElementById('case-grid');
const caseDetail = document.getElementById('case-detail');
const subspecialtyFilter = document.getElementById('subspecialty-filter');
const searchInput = document.getElementById('search-input');
const themeToggle = document.getElementById('theme-toggle');
const backBtn = document.getElementById('back-btn');
const caseTitle = document.getElementById('case-title');
const caseCitation = document.getElementById('case-citation');
const caseCount = document.getElementById('case-count');
const sessionCount = document.getElementById('session-count');
const mcqCount = document.getElementById('mcq-count');
const requestDatasetLink = document.getElementById('request-dataset-link');
const tabBtns = document.querySelectorAll('.tab-btn');
const modelColumns = document.querySelectorAll('.model-column');
const restrictedOverlay = document.getElementById('restricted-overlay');
const stats = document.querySelector('.stats');
const filters = document.querySelector('.filters');

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initEventListeners();
    loadCaseIndex();
});

async function loadCaseIndex() {
    try {
        const url = new URL(`${API_BASE}/api/cases`);
        if (accessToken) url.searchParams.set('access', accessToken);

        const response = await fetch(url);
        caseIndex = await response.json();
        initFilters();
        renderCaseGrid();
    } catch (error) {
        console.error('Failed to load case index:', error);
        caseGrid.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 40px;">Failed to load data. Please try again later.</p>';
    }
}

// ===== Theme =====
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// ===== Event Listeners =====
function initEventListeners() {
    themeToggle.addEventListener('click', toggleTheme);
    subspecialtyFilter.addEventListener('change', filterAndRender);
    searchInput.addEventListener('input', debounce(filterAndRender, 300));
    backBtn.addEventListener('click', showCaseGrid);

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const question = btn.dataset.question;

            // If locked (unauthorized), show visual feedback but don't switch
            if (btn.classList.contains('locked')) {
                btn.style.transform = 'scale(0.98)';
                setTimeout(() => btn.style.transform = '', 150);
                return;
            }

            // Switch view between MCQ and Evaluation
            if (question === 'eval') {
                currentView = 'eval';
            } else {
                currentView = 'mcq';
                selectedMcq = parseInt(question);
            }

            // Update active state
            tabBtns.forEach(b => {
                b.classList.remove('active');
            });
            btn.classList.add('active');

            renderModelComparison();
        });
    });
}

// ===== Filters =====
function initFilters() {
    const subspecialties = [...new Set(caseIndex.map(c => c.subspecialty))].sort();

    subspecialties.forEach(sub => {
        const option = document.createElement('option');
        option.value = sub;
        option.textContent = sub;
        subspecialtyFilter.appendChild(option);
    });
}

function filterAndRender() {
    // Dropdown Fix: Always navigate back to grid when filtering
    showCaseGrid();

    const subspecialty = subspecialtyFilter.value;
    const searchTerm = searchInput.value.toLowerCase();

    filteredCases = caseIndex.filter(c => {
        if (subspecialty && c.subspecialty !== subspecialty) return false;
        if (searchTerm) {
            const searchable = `${c.case_id} ${c.case_title} ${c.subspecialty}`.toLowerCase();
            if (!searchable.includes(searchTerm)) return false;
        }
        return true;
    });

    renderCaseGrid();
}

// ===== Render Case Grid =====
function renderCaseGrid() {
    const casesToRender = filteredCases.length > 0 ? filteredCases : caseIndex;

    caseCount.textContent = `${casesToRender.length} cases`;
    sessionCount.textContent = `${casesToRender.length * 4} sessions`;
    mcqCount.textContent = `${casesToRender.length * 4 * 3} MCQs`;

    caseGrid.innerHTML = casesToRender.map(c => `
        <div class="case-card" data-case-id="${c.case_id}">
            <div class="case-card-header">
                <span class="case-id">ID: ${c.case_id}</span>
                <span class="subspecialty-badge">${shortenSubspecialty(c.subspecialty)}</span>
            </div>
            <h3 class="case-title">${c.case_title.replace(/\\/g, '')}</h3>
            <div class="case-models">
                <span class="model-dot gpt4o" title="GPT-4o"></span>
                <span class="model-dot claude" title="Claude 3.5"></span>
                <span class="model-dot gemini" title="Gemini 1.5"></span>
                <span class="model-dot llama" title="Llama 3-70b"></span>
            </div>
        </div>
    `).join('');

    document.querySelectorAll('.case-card').forEach(card => {
        card.addEventListener('click', async () => {
            currentCaseId = parseInt(card.dataset.caseId);
            await showCaseDetail();
        });
    });
}

function shortenSubspecialty(sub) {
    const shortNames = {
        'Breast Imaging': 'Breast',
        'Cardiovascular Imaging': 'Cardiovascular',
        'Gastrointestinal & Hepatobiliary Imaging': 'GI/Hepatobiliary',
        'Interventional Radiology': 'IR',
        'Musculoskeletal Imaging': 'MSK',
        'Neuroradiology & HFN': 'Neuro/HFN',
        'Pediatric & Emergency Radiology': 'Peds/Emergency',
        'Thoracic Imaging': 'Thoracic',
        'Urogenital Imaging': 'Urogenital',
        'Physics': 'Physics'
    };
    return shortNames[sub] || sub;
}

// ===== Case Detail View =====
async function showCaseDetail() {
    caseGrid.classList.add('hidden');
    caseDetail.classList.remove('hidden');

    // Show loading state
    modelColumns.forEach(col => {
        col.querySelector('.model-content').innerHTML = '<p class="loading">Loading...</p>';
    });

    try {
        const url = new URL(`${API_BASE}/api/case/${currentCaseId}`);
        if (accessToken) url.searchParams.set('access', accessToken);

        const response = await fetch(url);
        currentCaseData = await response.json();

        // Update header
        caseTitle.textContent = `Case ${currentCaseId} - ${currentCaseData.subspecialty}`;
        caseCitation.innerHTML = formatCitation(currentCaseData.citation);

        // Hybrid Access Check
        const isRestricted = currentCaseData.access_restricted;

        if (isRestricted) {
            restrictedOverlay.classList.remove('hidden');
            tabBtns.forEach(btn => {
                btn.classList.remove('active');
                btn.classList.add('locked');
                const label = btn.dataset.question === 'eval' ? 'Evaluation' : `MCQ ${btn.dataset.question}`;
                btn.innerHTML = `${label} 🔒`;
            });
        } else {
            restrictedOverlay.classList.add('hidden');
            selectedMcq = 1;
            currentView = 'mcq';

            tabBtns.forEach(btn => {
                const question = btn.dataset.question;
                const isFirstMcq = question === "1";
                const isEval = question === 'eval';

                btn.classList.remove('active', 'locked');
                if (isFirstMcq) btn.classList.add('active');
                if (!isEval) btn.innerHTML = `MCQ ${question}`;
                else btn.innerHTML = 'Evaluation';
            });
        }

        renderModelComparison();
    } catch (error) {
        console.error('Failed to load case:', error);
        modelColumns.forEach(col => {
            col.querySelector('.model-content').innerHTML = '<em>Failed to load data</em>';
        });
    }
}

function showCaseGrid() {
    caseDetail.classList.add('hidden');
    caseGrid.classList.remove('hidden');
    currentCaseId = null;
    currentCaseData = null;
}

function renderModelComparison() {
    if (!currentCaseData || currentCaseData.access_restricted) {
        // Clear content if restricted
        modelColumns.forEach(column => {
            column.querySelector('.model-content').innerHTML = '';
        });
        return;
    }

    const mcqKey = `mcq_${selectedMcq}`;

    modelColumns.forEach(column => {
        const modelId = column.dataset.model;
        const modelData = currentCaseData.models[modelId];
        const contentDiv = column.querySelector('.model-content');

        if (!modelData) {
            contentDiv.innerHTML = '<em>No data available</em>';
            return;
        }

        if (currentView === 'eval') {
            const evaluation = modelData.osce_session ? modelData.osce_session.evaluation : '';
            contentDiv.innerHTML = evaluation ? formatContent(evaluation) : '<em>No evaluation available</em>';
        } else {
            const mcq = modelData.osce_session ? modelData.osce_session[mcqKey] : null;
            if (mcq) {
                let content = formatContent(mcq.content);
                content += `<div class="random-answer">Random Answer: ${mcq.random_answer}</div>`;
                contentDiv.innerHTML = content;
            } else {
                contentDiv.innerHTML = '<em>No data available</em>';
            }
        }
    });
}

function isFullAccessMode() {
    return !currentCaseData || !currentCaseData.access_restricted;
}

function formatContent(text) {
    if (!text) return '<em>No content</em>';

    return text
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
        .replace(/^/, '<p>')
        .replace(/$/, '</p>');
}

function formatCitation(citation) {
    if (!citation) return '';
    return citation
        .replace(/\\\[/g, '[')
        .replace(/\\\]/g, ']')
        .replace(/\[([^\]]+)\]\(\[?([^\)\]]+)\]?\(?([^\)]*)?(\)?\))/g, (match, text, url1, url2) => {
            const url = url2 || url1;
            return `<a href="${url}" target="_blank" rel="noopener">${text}</a>`;
        })
        .replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
}

// ===== Utilities =====
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
