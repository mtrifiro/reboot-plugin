import { useEffect, useRef, useState, type MouseEvent, type ReactNode } from "react";

// The contents pattern for a long scrolling page (ui-design.md, 03): a
// sidebar listing the page's own sections, the one being read marked,
// that stays in view under the top bar. From 640 px up it is a column
// beside the page; below that it folds into a "Contents" panel at the
// top. The entries are the `h2` and `h3` headings with an `id` inside
// the page body, read again whenever the body changes, so live sections
// join the list as they render.
//
//   <WithContents>
//     <section><h2 id="rooms">Rooms</h2>…</section>
//     <section><h2 id="stays">Stays</h2>…</section>
//   </WithContents>

type Entry = { id: string; text: string; depth: number };

const WIDE = "(min-width: 640px)";

export function WithContents({ label = "Contents", children }: { label?: string; children: ReactNode }) {
  const body = useRef<HTMLDivElement>(null);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [active, setActive] = useState<string>();
  const [open, setOpen] = useState(() => window.matchMedia(WIDE).matches);

  // The headings, read from the page body and again as it changes.
  useEffect(() => {
    const element = body.current;
    if (!element) return;
    const read = () => {
      const found = Array.from(element.querySelectorAll<HTMLElement>("h2[id], h3[id]")).map((h) => ({
        id: h.id,
        text: h.textContent?.trim() ?? "",
        depth: h.tagName === "H3" ? 3 : 2,
      }));
      setEntries((was) =>
        was.length === found.length && was.every((e, i) => e.id === found[i].id && e.text === found[i].text) ? was : found,
      );
    };
    read();
    const observer = new MutationObserver(read);
    observer.observe(element, { childList: true, subtree: true, characterData: true });
    return () => observer.disconnect();
  }, []);

  // Open beside the page wherever there is room, folded below 640 px; it
  // follows the window as it is resized.
  useEffect(() => {
    const query = window.matchMedia(WIDE);
    const onChange = () => setOpen(query.matches);
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);

  // The section being read: the last heading above the upper third of the
  // screen, or the last one once the page is scrolled to its end.
  useEffect(() => {
    const onScroll = () => {
      const atEnd = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4;
      if (atEnd) {
        setActive(entries[entries.length - 1]?.id);
        return;
      }
      let current: string | undefined;
      for (const entry of entries) {
        const heading = document.getElementById(entry.id);
        if (heading && heading.getBoundingClientRect().top < window.innerHeight * 0.35) current = entry.id;
      }
      setActive(current ?? entries[0]?.id);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [entries]);

  const jump = (id: string) => (event: MouseEvent) => {
    event.preventDefault();
    document.getElementById(id)?.scrollIntoView({ block: "start" });
    history.replaceState(null, "", `#${id}`);
    setActive(id);
    if (!window.matchMedia(WIDE).matches) setOpen(false);
  };

  return (
    <div className="with-contents">
      {entries.length > 0 && (
        <aside className="toc" aria-label={label}>
          <details open={open} onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}>
            <summary>{label}</summary>
            <ol>
              {entries.map((entry) => (
                <li key={entry.id} className={`toc-depth-${entry.depth}`}>
                  <a
                    href={`#${entry.id}`}
                    onClick={jump(entry.id)}
                    aria-current={entry.id === active ? "location" : undefined}
                    className={entry.id === active ? "active" : undefined}
                  >
                    {entry.text}
                  </a>
                </li>
              ))}
            </ol>
          </details>
        </aside>
      )}
      <div ref={body} className="contents-body">
        {children}
      </div>
    </div>
  );
}
