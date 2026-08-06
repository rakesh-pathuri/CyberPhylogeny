// Initialize Mermaid
mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    securityLevel: 'loose',
    fontFamily: 'Inter, sans-serif'
});

// Tab Navigation Logic
document.querySelectorAll('header .tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('header .tab-btn').forEach(b => b.classList.remove('active'));
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

// API Callers
async function fetchGenome() {
    const id = document.getElementById('genome-id-input').value.trim();
    if (!id) return;
    
    const out = document.getElementById('genome-output');
    out.innerHTML = `<div class="placeholder-text">FETCHING DATA...</div>`;
    
    try {
        const res = await fetch(`/api/genome?id=${id}`);
        const data = await res.json();
        
        if (data.error) {
            out.innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
            return;
        }
        
        let html = `<h3>Genome Profile: ${data.name} (${id})</h3>`;
        html += `<table>
            <tr>
                <th>Index</th>
                <th>Technique ID</th>
                <th>Implementation</th>
                <th>Behavior</th>
                <th>Tactic</th>
            </tr>`;
            
        data.genes.forEach((g, idx) => {
            html += `<tr>
                <td>${idx + 1}</td>
                <td>${g.technique_id}</td>
                <td>${g.implementation}</td>
                <td>${g.behavior}</td>
                <td>${g.tactic}</td>
            </tr>`;
        });
        html += `</table>`;
        out.innerHTML = html;
        
    } catch (e) {
        out.innerHTML = `<p style="color:red;">API Request Failed.</p>`;
    }
}

async function fetchFamilies() {
    const out = document.getElementById('family-list-output');
    
    try {
        const res = await fetch(`/api/cluster`);
        const data = await res.json();
        
        if (data.error) {
            out.innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
            return;
        }
        
        out.innerHTML = '';
        data.families.forEach(f => {
            const card = document.createElement('div');
            card.className = 'family-card';
            card.innerHTML = `
                <h3>FAMILY ${f.id}</h3>
                <p style="font-family: var(--font-mono); font-size: 12px; color: #888;">${f.size} variants</p>
                <button style="margin-top: 10px; width: 100%;" onclick="loadTreeFromFamily('${f.id}')">VIEW PHYLOGENY</button>
            `;
            out.appendChild(card);
        });
        
    } catch (e) {
        out.innerHTML = `<p style="color:red;">API Request Failed.</p>`;
    }
}

function loadTreeFromFamily(familyId) {
    document.querySelector('header .tab-btn[data-tab="tab-trees"]').click();
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
    outMermaid.innerHTML = '<div class="placeholder-text">COMPUTING MST...</div>';
    stats.innerHTML = 'STATUS: COMPUTING...';
    
    try {
        const res = await fetch(`/api/tree?family=${id}`);
        const data = await res.json();
        
        if (data.error) {
            outAscii.innerHTML = `Error: ${data.error}`;
            outMermaid.innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
            stats.innerHTML = 'STATUS: ERROR';
            return;
        }
        
        stats.innerHTML = 'STATUS: RENDERED';
        
        // Render ASCII
        outAscii.textContent = data.ascii;
        
        // Render Mermaid
        outMermaid.innerHTML = `<div class="mermaid" id="mermaid-graph"></div>`;
        const graphDiv = document.getElementById('mermaid-graph');
        const { svg } = await mermaid.render('mermaid-svg', data.mermaid);
        graphDiv.innerHTML = svg;
        
    } catch (e) {
        outAscii.innerHTML = 'API Request Failed.';
        outMermaid.innerHTML = `<p style="color:red;">API Request Failed.</p>`;
        stats.innerHTML = 'STATUS: FAILED';
    }
}

async function fetchPrediction() {
    const seq = document.getElementById('predict-seq-input').value.trim();
    if (!seq) return;
    
    const out = document.getElementById('predict-output');
    out.innerHTML = `<div class="placeholder-text">CALCULATING PROBABILITIES...</div>`;
    
    try {
        const res = await fetch(`/api/predict?seq=${encodeURIComponent(seq)}`);
        const data = await res.json();
        
        if (data.error) {
            out.innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
            return;
        }
        
        if (data.predictions.length === 0) {
            out.innerHTML = `<p style="color:yellow;">No highly probable sequences found.</p>`;
            return;
        }
        
        let html = `<table>
            <tr>
                <th>Predicted Technique ID</th>
                <th>Implementation</th>
                <th>Behavior</th>
                <th>Tactic</th>
                <th>Probability</th>
                <th>Confidence Score</th>
            </tr>`;
            
        data.predictions.forEach(p => {
            html += `<tr>
                <td style="color:var(--accent); font-weight:bold;">${p.technique_id}</td>
                <td>${p.implementation}</td>
                <td>${p.behavior}</td>
                <td>${p.tactic}</td>
                <td style="color:var(--accent);">${p.probability}</td>
                <td>${p.confidence}</td>
            </tr>`;
        });
        html += `</table>`;
        out.innerHTML = html;
        
    } catch (e) {
        out.innerHTML = `<p style="color:red;">API Request Failed.</p>`;
    }
}

// Boot
window.onload = () => {
    fetchFamilies(); // load families automatically on startup
};
