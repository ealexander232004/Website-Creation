"use client";

import { useEffect } from "react";

export function MotionObserver() {
  useEffect(() => {
    const observed = new WeakSet<Element>();

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      document.querySelectorAll<HTMLElement>("[data-reveal]").forEach((target) => target.classList.add("is-visible"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -10%", threshold: 0.12 },
    );

    function registerTargets(root: ParentNode) {
      root.querySelectorAll<HTMLElement>("[data-reveal]").forEach((target) => {
        if (!observed.has(target)) {
          observed.add(target);
          observer.observe(target);
        }
      });
    }

    registerTargets(document);

    const mutationObserver = new MutationObserver((entries) => {
      entries.forEach((entry) => {
        entry.addedNodes.forEach((node) => {
          if (node instanceof HTMLElement) {
            if (node.matches("[data-reveal]") && !observed.has(node)) {
              observed.add(node);
              observer.observe(node);
            }
            registerTargets(node);
          }
        });
      });
    });

    mutationObserver.observe(document.body, { childList: true, subtree: true });

    return () => {
      mutationObserver.disconnect();
      observer.disconnect();
    };
  }, []);

  return null;
}
