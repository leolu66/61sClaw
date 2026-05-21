import { chromium } from "playwright";

const url = process.argv[2] || "https://www.toutiao.com/video/7634869978763756084/";

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
  });
  const page = await context.newPage();
  
  try {
    await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
    await page.waitForTimeout(3000);
    
    // Get the page body text
    const bodyText = await page.evaluate(() => {
      // Get visible text content
      const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
        {
          acceptNode: (node) => {
            const parent = node.parentElement;
            if (!parent) return NodeFilter.FILTER_REJECT;
            const style = window.getComputedStyle(parent);
            if (style.display === "none" || style.visibility === "hidden") {
              return NodeFilter.FILTER_REJECT;
            }
            return NodeFilter.FILTER_ACCEPT;
          }
        }
      );
      
      const texts = [];
      let node;
      while ((node = walker.nextNode())) {
        const t = node.textContent.trim();
        if (t) texts.push(t);
      }
      return texts.join("\n").substring(0, 5000);
    });
    
    console.log("=== PAGE TEXT ===");
    console.log(bodyText);
    console.log("=== END ===");
    
  } catch (e) {
    console.error("Error:", e.message);
  }
  
  await browser.close();
})();
