# Introduction

Convert web pages to Markdown.

# Why?

Easier and more efficient way to feed documentation into LLM agents such as Claude Code and gemini-cli.
Websearches could be slow, inefficient, billed separately and by default summarise the page.

Converting webpages to PDF can be very poor OOTB or require browser plugin or extension. PDF also consume hell lot of tokens, in hundreds of thousands for relatively simple technical design page.

The tools in this folder convert documentation pages to Markdown files containing word for work information and preserving images and codeblocks.

# Tools

## Browser Snippet

Save the Snippet:

1. Press F12 to open Developer Tools.

2. Click the Sources tab (top panel).

3. In the left sidebar, look for the Snippets tab. (If you don't see it, click the double arrow >> next to "Page" or "Filesystem").

4. Click + New Snippet.

5. Paste script


## Bookmarklet

```
javascript:(function(){var s=document.createElement('script');s.src='https://unpkg.com/@mozilla/readability@0.5.0/Readability.js';document.head.appendChild(s);s.onload=function(){var t=document.createElement('script');t.src='https://unpkg.com/turndown/dist/turndown.js';document.head.appendChild(t);t.onload=function(){var u=document.createElement('script');u.src='https://unpkg.com/turndown-plugin-gfm/dist/turndown-plugin-gfm.js';document.head.appendChild(u);u.onload=function(){var a=new Readability(document.cloneNode(true)).parse();var ts=new TurndownService({headingStyle:'atx',codeBlockStyle:'fenced'});ts.use(turndownPluginGfm.gfm);var m="# "+a.title+"\nSource: "+window.location.href+"\n\n---\n\n"+ts.turndown(a.content);navigator.clipboard.writeText(m);var b=new Blob([m],{type:'text/markdown'});var l=document.createElement('a');l.href=URL.createObjectURL(b);l.download=a.title.replace(/[^a-z0-9]/gi,'_').toLowerCase()+".md";document.body.appendChild(l);l.click();l.remove();alert("Markdown downloaded & copied to clipboard!");}}}})();
```


## ADK Agent

Works beautifully using a small model to understand and parse the page rather than programatic page parsing. Each page can be slightly different and there is a (small) chance that it may not work on some pages.

This was primarily exercise in ADK and Vertex AI Agent Engine, but it was easy and does produce good results every time. Source code in `adk-converter` folder
