// Initialize Mermaid
mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    securityLevel: 'loose',
    fontFamily: 'Inter, sans-serif'
});

// Tab Navigation Logic
document.querySelectorAll('.soc-header .tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.soc-header .tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        btn.classList.add('active');
        const targetId = btn.getAttribute('data-tab');
        document.getElementById(targetId).classList.add('active');
    });
});

// Tree View Switcher Logic
function switchTreeView(mode) {
    document.getElementById('btn-view-ascii').classList.remove('active');
    document.getElementById('btn-view-mermaid').classList.remove('active');
    document.getElementById('tree-output-ascii').classList.remove('active');
    document.getElementById('tree-output-mermaid').classList.remove('active');
    
    document.getElementById(`btn-view-${mode}`).classList.add('active');
    document.getElementById(`tree-output-${mode}`).classList.add('active');
}

// Format Utilities
function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

function processAsciiTreeColors(text) {
    // Converts rich tags [green] [/green] and [red] [/red] to span tags
    let processed = text.replace(/\[green\]/g, '<span style="color: var(--success);">');
    processed = processed.replace(/\[\/green\]/g, '</span>');
    processed = processed.replace(/\[red\]/g, '<span style="color: var(--danger);">');
    processed = processed.replace(/\[\/red\]/g, '</span>');
    return processed;
}

// API Callers
async function fetchGenome() {
    const id = document.getElementById('genome-id-input').value.trim();
    if (!id) return;
    
    const out = document.getElementById('genome-output');
    out.innerHTML = `<div class="empty-state blink">QUERYING KNOWLEDGE BASE...</div>`;
    
    try {
        const res = await fetch(`/api/genome?id=${id}`);
        const data = await res.json();
        
        if (data.error) {
            out.innerHTML = `<div class="empty-state" style="color: var(--danger);">ERROR: ${data.error.toUpperCase()}</div>`;
            return;
        }
        
        let html = `<div class="table-wrapper">
            <table>
            <thead>
                <tr>
                    <th style="width: 50px;">Idx</th>
                    <th style="width: 120px;">Technique ID</th>
                    <th>Implementation</th>
                    <th>Behavior</th>
                    <th>Tactic</th>
                </tr>
            </thead>
            <tbody>`;
            
        data.genes.forEach((g, idx) => {
            html += `<tr>
                <td class="mono" style="color: var(--text-secondary);">${String(idx + 1).padStart(2, '0')}</td>
                <td class="mono highlight">${g.technique_id}</td>
                <td>${escapeHtml(g.implementation)}</td>
                <td>${escapeHtml(g.behavior)}</td>
                <td style="color: var(--text-secondary);">${escapeHtml(g.tactic)}</td>
            </tr>`;
        });
        html += `</tbody></table></div>`;
        out.innerHTML = html;
        
    } catch (e) {
        out.innerHTML = `<div class="empty-state" style="color: var(--danger);">API CONNECTION LOST</div>`;
    }
}

async function fetchFamilies() {
    const out = document.getElementById('family-list-output');
    out.innerHTML = `<div class="empty-state blink">CLUSTERING GENOMES...</div>`;
    
    try {
        const res = await fetch(`/api/cluster`);
        const data = await res.json();
        
        if (data.error) {
            out.innerHTML = `<div class="empty-state" style="color: var(--danger);">ERROR: ${data.error.toUpperCase()}</div>`;
            return;
        }
        
        out.innerHTML = '';
        data.families.forEach(f => {
            const card = document.createElement('div');
            card.className = 'family-card';
            card.innerHTML = `
                <h3>FAMILY ${f.id}</h3>
                <div class="stats">${f.size} VARIANTS DETECTED</div>
                <button onclick="loadTreeFromFamily('${f.id}')">VIEW PHYLOGENY</button>
            `;
            out.appendChild(card);
        });
        
    } catch (e) {
        out.innerHTML = `<div class="empty-state" style="color: var(--danger);">API CONNECTION LOST</div>`;
    }
}

function loadTreeFromFamily(familyId) {
    document.querySelector('.soc-header .tab-btn[data-tab="tab-trees"]').click();
    document.getElementById('tree-family-input').value = familyId;
    fetchTree();
}

async function fetchTree() {
    const id = document.getElementById('tree-family-input').value.trim();
    if (!id) return;
    
    const outAscii = document.querySelector('#tree-output-ascii pre');
    const outMermaid = document.querySelector('#tree-output-mermaid .mermaid-canvas');
    const stats = document.getElementById('tree-stats');
    
    outAscii.innerHTML = 'COMPUTING MST...';
    outMermaid.innerHTML = '<div class="empty-state blink">COMPUTING MST...</div>';
    stats.innerHTML = 'STATUS: COMPUTING...';
    stats.style.color = 'var(--text-secondary)';
    
    try {
        const res = await fetch(`/api/tree?family=${id}`);
        const data = await res.json();
        
        if (data.error) {
            outAscii.innerHTML = `ERROR: ${data.error.toUpperCase()}`;
            outMermaid.innerHTML = `<div class="empty-state" style="color: var(--danger);">ERROR: ${data.error.toUpperCase()}</div>`;
            stats.innerHTML = 'STATUS: FAILED';
            stats.style.color = 'var(--danger)';
            return;
        }
        
        stats.innerHTML = 'STATUS: OK';
        stats.style.color = 'var(--success)';
        
        // Render ASCII (escaped, then parsed for color tags)
        let safeAscii = escapeHtml(data.ascii);
        outAscii.innerHTML = processAsciiTreeColors(safeAscii);
        
        // Render Mermaid
        outMermaid.innerHTML = `<div class="mermaid" id="mermaid-graph"></div>`;
        const graphDiv = document.getElementById('mermaid-graph');
        const { svg } = await mermaid.render('mermaid-svg', data.mermaid);
        graphDiv.innerHTML = svg;
        
    } catch (e) {
        outAscii.innerHTML = 'API CONNECTION LOST';
        outMermaid.innerHTML = `<div class="empty-state" style="color: var(--danger);">API CONNECTION LOST</div>`;
        stats.innerHTML = 'STATUS: OFFLINE';
        stats.style.color = 'var(--danger)';
    }
}

async function fetchPrediction() {
    const seq = document.getElementById('predict-seq-input').value.trim();
    if (!seq) return;
    
    const out = document.getElementById('predict-output');
    out.innerHTML = `<div class="empty-state blink">ANALYZING SEQUENCE PROBABILITIES...</div>`;
    
    try {
        const res = await fetch(`/api/predict?seq=${encodeURIComponent(seq)}`);
        const data = await res.json();
        
        if (data.error) {
            out.innerHTML = `<div class="empty-state" style="color: var(--danger);">ERROR: ${data.error.toUpperCase()}</div>`;
            return;
        }
        
        if (data.predictions.length === 0) {
            out.innerHTML = `<div class="empty-state" style="color: var(--text-secondary);">NO SIGNIFICANT PREDICTIONS FOUND</div>`;
            return;
        }
        
        let html = `<div class="table-wrapper">
            <table>
            <thead>
                <tr>
                    <th style="width: 120px;">Technique ID</th>
                    <th>Implementation</th>
                    <th>Tactic</th>
                    <th style="width: 250px;">Probability</th>
                </tr>
            </thead>
            <tbody>`;
            
        data.predictions.forEach(p => {
            const probNum = parseFloat(p.probability);
            html += `<tr>
                <td class="mono highlight">${p.technique_id}</td>
                <td>${escapeHtml(p.implementation)}</td>
                <td style="color: var(--text-secondary);">${escapeHtml(p.tactic)}</td>
                <td>
                    <div style="display: flex; justify-content: space-between; font-family: var(--font-mono); font-size: 12px; margin-bottom: 2px;">
                        <span>${p.probability}</span>
                        <span style="color: var(--text-secondary);">${p.confidence} CONFIDENCE</span>
                    </div>
                    <div class="prob-bar-container">
                        <div class="prob-bar" style="width: ${Math.min(100, probNum)}%;"></div>
                    </div>
                </td>
            </tr>`;
        });
        html += `</tbody></table></div>`;
        out.innerHTML = html;
        
    } catch (e) {
        out.innerHTML = `<div class="empty-state" style="color: var(--danger);">API CONNECTION LOST</div>`;
    }
}

// Boot
window.onload = () => {
    fetchFamilies();
};
