// The top bar's page links, and the bar's height for what sits below
// it. Put `<SiteNav>` in the top bar right after the brand, before the
// `spacer`, once the app has two or more pages.
//
// The links never scroll out of sight. Four layouts, chosen by
// measuring, not by breakpoints, so the choice only ever moves one way
// as the window narrows:
//
// - "inline": beside the title, when they fit there;
// - "row": a second line of the bar to themselves;
// - "row-tight": that line with less space between links;
// - "menu": a menu button (☰ and the current page) left of the title,
//   when even a line of their own would cut them off.
//
// Hidden copies of the row, at both spacings and clipped to nothing,
// give its widths; `data-nav` on the bar carries the layout to the CSS.
// Nothing a layout changes may reach those copies: a measurement that
// depends on what it chooses flips between two layouts at one width.
import { type RefObject, useEffect, useLayoutEffect, useRef, useState } from "react";

export type NavItem = { href: string; label: string; active: boolean };
type Layout = "inline" | "row" | "row-tight" | "menu";

// Keeps `--topbar-h` at the bar's real height (it grows when the links
// take a second line): sticky table heads, side panels and menus sit
// below it. The bar's own `min-height` is a number, never this
// variable, or each would push the other up.
export function useBarHeight(bar: RefObject<HTMLElement>) {
  useEffect(() => {
    const element = bar.current;
    if (!element) return;
    const observer = new ResizeObserver(() => {
      document.documentElement.style.setProperty("--topbar-h", `${element.offsetHeight}px`);
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, [bar]);
}

// The room in the bar: its whole inner width (a line of its own), and
// what is left beside everything else on the first line.
function room(bar: HTMLElement, slot: HTMLElement): { line: number; beside: number } {
  const style = getComputedStyle(bar);
  const line = bar.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
  const gap = parseFloat(style.columnGap) || 0;
  const others = [...bar.children].filter((child) => child !== slot) as HTMLElement[];
  const spacers = others.filter((child) => child.classList.contains("spacer"));
  const taken = others.filter((child) => !spacers.includes(child)).reduce((sum, child) => sum + child.offsetWidth, 0);
  return { line, beside: line - taken - gap * others.length };
}

export function SiteNav({ items }: { items: NavItem[] }) {
  const slot = useRef<HTMLDivElement>(null);
  const normal = useRef<HTMLDivElement>(null);
  const tight = useRef<HTMLDivElement>(null);
  const [layout, setLayout] = useState<Layout>("inline");

  useLayoutEffect(() => {
    const bar = slot.current?.parentElement;
    const fit = () => {
      if (!bar || !slot.current || !normal.current || !tight.current) return;
      const { line, beside } = room(bar, slot.current);
      const width = normal.current.scrollWidth;
      const next: Layout =
        width <= beside ? "inline" : width <= line ? "row" : tight.current.scrollWidth <= line ? "row-tight" : "menu";
      bar.dataset.nav = next;
      setLayout(next);
    };
    fit();
    // The bar (the window's width) and the copies (fonts loading).
    const observer = new ResizeObserver(fit);
    for (const element of [bar, normal.current, tight.current]) if (element) observer.observe(element);
    return () => observer.disconnect();
  }, []);

  const copy = (ref: RefObject<HTMLDivElement>, className: string) => (
    <div className={className} ref={ref}>
      {items.map((item) => (
        <span key={item.href}>{item.label}</span>
      ))}
    </div>
  );
  return (
    <div className="nav-slot" ref={slot}>
      <div className="nav-measure-box" aria-hidden="true">
        {copy(normal, "nav-measure")}
        {copy(tight, "nav-measure tight")}
      </div>
      {layout === "menu" ? (
        <NavMenu items={items} />
      ) : (
        <nav className="site-nav" aria-label="Pages">
          {items.map((item) => (
            <a key={item.href} href={item.href} className={item.active ? "active" : undefined} aria-current={item.active ? "page" : undefined}>
              {item.label}
            </a>
          ))}
        </nav>
      )}
    </div>
  );
}

function NavMenu({ items }: { items: NavItem[] }) {
  const [open, setOpen] = useState(false);
  const menu = useRef<HTMLDivElement>(null);
  const current = items.find((item) => item.active);

  // Choosing a page closes it; so do Esc and a click outside.
  useEffect(() => setOpen(false), [current?.href]);
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    const onDown = (event: PointerEvent) => {
      if (menu.current && !menu.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onDown);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onDown);
    };
  }, [open]);

  return (
    <div className="nav-menu" ref={menu}>
      <button
        className="ghost nav-menu-button"
        aria-label="Menu"
        aria-expanded={open}
        aria-controls="nav-menu-panel"
        onClick={() => setOpen(!open)}
      >
        <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" style={{ display: "block" }}>
          <path d={open ? "M6 6l12 12M18 6L6 18" : "M4 6h16M4 12h16M4 18h16"} />
        </svg>
        {current && <span className="nav-menu-current">{current.label}</span>}
      </button>
      {open && (
        <nav className="nav-menu-panel" id="nav-menu-panel" aria-label="Pages">
          {items.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className={item.active ? "active" : undefined}
              aria-current={item.active ? "page" : undefined}
              onClick={() => setOpen(false)}
            >
              {item.label}
            </a>
          ))}
        </nav>
      )}
    </div>
  );
}
