(async function() {
    console.log("⏳ Initializing Markdown extractor...");

    // Helper to load external libraries dynamically
    const loadScript = (src) => new Promise((resolve, reject) => {
        if (document.querySelector(`script[src="${src}"]`)) return resolve();
        const s = document.createElement('script');
        s.src = src;
        s.onload = resolve;
        s.onerror = reject;
        document.head.appendChild(s);
    });

    try {
        // 1. Load Readability (cleans the page) and Turndown (converts to MD)
        await loadScript('https://unpkg.com/@mozilla/readability@0.5.0/Readability.js');
        await loadScript('https://unpkg.com/turndown/dist/turndown.js');
        await loadScript('https://unpkg.com/turndown-plugin-gfm/dist/turndown-plugin-gfm.js');

        console.log("✅ Libraries loaded. Parsing content...");

        // 2. Extract Main Content (removes nav bars, ads, footers)
        // We clone the document so we don't mess up the actual page view
        const documentClone = document.cloneNode(true);
        const reader = new Readability(documentClone);
        const article = reader.parse();

        if (!article) throw new Error("Could not detect main content.");

        // 3. Configure Markdown Conversion
        const turndownService = new TurndownService({
            headingStyle: 'atx',      // Use # for headings
            codeBlockStyle: 'fenced'  // Use ``` for code blocks
        });

        // Add GitHub Flavored Markdown (better tables & task lists)
        const gfm = turndownPluginGfm.gfm;
        turndownService.use(gfm);

        // 4. Convert to Markdown
        // We add the Title and URL at the top for context
        const header = `# ${article.title}\nSource: ${window.location.href}\n\n---\n\n`;
        const markdown = header + turndownService.turndown(article.content);

        // 5. Trigger Download
        const blob = new Blob([markdown], { type: 'text/markdown' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `${article.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        console.log("🎉 Markdown file downloaded!");

    } catch (err) {
        console.error("❌ Extraction failed:", err);
    }
})();
