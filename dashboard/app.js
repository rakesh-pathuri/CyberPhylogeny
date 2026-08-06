// Initialize Mermaid with dark theme
mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    securityLevel: 'loose',
    fontFamily: 'Inter, sans-serif'
});

let evolutionaryData = {};

// Fetch JSON data
async function loadData() {
    try {
        const response = await fetch('data.json');
        evolutionaryData = await response.json();
        populateSidebar();
    } catch (error) {
        console.error("Failed to load evolutionary data:", error);
        document.getElementById('family-list').innerHTML = `<p style="color: red;">Error loading data.json</p>`;
    }
}

// Populate the sidebar with families
function populateSidebar() {
    const listContainer = document.getElementById('family-list');
    listContainer.innerHTML = ''; // clear

    const families = Object.keys(evolutionaryData).sort((a, b) => Number(a) - Number(b));

    families.forEach(familyId => {
        const data = evolutionaryData[familyId];
        const btn = document.createElement('button');
        btn.className = 'family-btn';
        btn.innerHTML = `FAMILY [${familyId}] <span style="float:right; opacity: 0.5;">${data.size} variants</span>`;
        
        btn.onclick = () => {
            // Update active state
            document.querySelectorAll('.family-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Render Tree
            renderTree(familyId, data.mermaid, data.size);
        };
        
        listContainer.appendChild(btn);
    });
}

// Render the Mermaid diagram
async function renderTree(familyId, mermaidStr, size) {
    document.getElementById('current-family-title').innerText = `FAMILY ${familyId} PHYLOGENY`;
    document.getElementById('meta-stats').innerText = `VARIANTS: ${size} | STATUS: COMPUTED`;
    
    const container = document.getElementById('mermaid-container');
    container.innerHTML = `<div class="mermaid" id="mermaid-graph"></div>`;
    
    const graphDiv = document.getElementById('mermaid-graph');
    
    try {
        const { svg } = await mermaid.render('mermaid-svg', mermaidStr);
        graphDiv.innerHTML = svg;
    } catch (error) {
        console.error("Mermaid rendering failed", error);
        graphDiv.innerHTML = `<p style="color: red;">Failed to render graph.</p>`;
    }
}

// Boot
window.onload = loadData;
