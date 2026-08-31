"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

const POINT_COUNT = 1500;

function fillShape(target: Float32Array, shape: "sphere" | "helix" | "tunnel") {
  for (let index = 0; index < POINT_COUNT; index += 1) {
    const offset = index * 3;
    const seed = index / POINT_COUNT;

    if (shape === "sphere") {
      const phi = Math.acos(1 - 2 * seed);
      const theta = Math.PI * (1 + Math.sqrt(5)) * index;
      const radius = 2.15 + Math.sin(index * 1.7) * 0.09;
      target[offset] = radius * Math.sin(phi) * Math.cos(theta);
      target[offset + 1] = radius * Math.cos(phi);
      target[offset + 2] = radius * Math.sin(phi) * Math.sin(theta);
    } else if (shape === "helix") {
      const angle = seed * Math.PI * 18;
      const strand = index % 2 === 0 ? 0 : Math.PI;
      target[offset] = Math.cos(angle + strand) * 1.55;
      target[offset + 1] = (seed - 0.5) * 6;
      target[offset + 2] = Math.sin(angle + strand) * 1.55;
    } else {
      const ring = Math.floor(index / 50);
      const point = index % 50;
      const angle = (point / 50) * Math.PI * 2 + ring * 0.16;
      const radius = 0.55 + ring * 0.095;
      target[offset] = Math.cos(angle) * radius;
      target[offset + 1] = Math.sin(angle) * radius;
      target[offset + 2] = (ring - 15) * 0.34;
    }
  }
}

export function ScrollExperience() {
  const sectionRef = useRef<HTMLElement>(null);
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mount = mountRef.current;
    const section = sectionRef.current;
    if (!mount || !section) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x050505, 0.085);

    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 40);
    camera.position.set(0, 0, 7.2);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.7));
    renderer.setClearColor(0x050505, 0);
    mount.appendChild(renderer.domElement);

    const sphere = new Float32Array(POINT_COUNT * 3);
    const helix = new Float32Array(POINT_COUNT * 3);
    const tunnel = new Float32Array(POINT_COUNT * 3);
    const positions = new Float32Array(POINT_COUNT * 3);
    const colors = new Float32Array(POINT_COUNT * 3);
    fillShape(sphere, "sphere");
    fillShape(helix, "helix");
    fillShape(tunnel, "tunnel");
    positions.set(sphere);

    const violet = new THREE.Color("#7568ff");
    const white = new THREE.Color("#f7f7f4");
    const lime = new THREE.Color("#c9ff3b");
    for (let index = 0; index < POINT_COUNT; index += 1) {
      const color = index % 29 === 0 ? lime : index % 4 === 0 ? white : violet;
      color.toArray(colors, index * 3);
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    const material = new THREE.PointsMaterial({
      size: 0.045,
      sizeAttenuation: true,
      transparent: true,
      opacity: 0.88,
      vertexColors: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    const points = new THREE.Points(geometry, material);
    scene.add(points);

    const rings = new THREE.Group();
    for (let index = 0; index < 5; index += 1) {
      const ringGeometry = new THREE.TorusGeometry(2.55 + index * 0.22, 0.006, 6, 150);
      const ringMaterial = new THREE.MeshBasicMaterial({
        color: index === 4 ? 0xc9ff3b : 0x7568ff,
        transparent: true,
        opacity: 0.15 + index * 0.025,
      });
      const ring = new THREE.Mesh(ringGeometry, ringMaterial);
      ring.rotation.set(index * 0.38, index * 0.55, index * 0.14);
      rings.add(ring);
    }
    scene.add(rings);

    let progress = 0;
    let visible = true;
    let frame = 0;

    const updateProgress = () => {
      const top = section.offsetTop;
      const distance = Math.max(section.offsetHeight - window.innerHeight, 1);
      progress = Math.min(1, Math.max(0, (window.scrollY - top) / distance));
    };

    const resize = () => {
      const { width, height } = mount.getBoundingClientRect();
      renderer.setSize(width, height, false);
      camera.aspect = width / Math.max(height, 1);
      camera.updateProjectionMatrix();
    };

    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
    });
    observer.observe(section);
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(mount);
    window.addEventListener("scroll", updateProgress, { passive: true });
    updateProgress();
    resize();

    const render = (time = 0) => {
      if (visible) {
        const local = progress < 0.5 ? progress * 2 : (progress - 0.5) * 2;
        const from = progress < 0.5 ? sphere : helix;
        const to = progress < 0.5 ? helix : tunnel;
        const eased = local * local * (3 - 2 * local);
        for (let index = 0; index < positions.length; index += 1) {
          positions[index] = from[index] + (to[index] - from[index]) * eased;
        }
        geometry.attributes.position.needsUpdate = true;

        const drift = reducedMotion ? 0 : time * 0.00008;
        points.rotation.y = progress * Math.PI * 1.8 + drift;
        points.rotation.x = progress * 0.7 - 0.2;
        rings.rotation.y = -progress * Math.PI * 1.2 - drift * 1.4;
        rings.rotation.x = progress * 0.55;
        rings.scale.setScalar(1 - progress * 0.12);
        camera.position.z = 7.2 - progress * 1.4;
        renderer.render(scene, camera);
      }
      if (!reducedMotion) frame = requestAnimationFrame(render);
    };
    render();

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", updateProgress);
      observer.disconnect();
      resizeObserver.disconnect();
      geometry.dispose();
      material.dispose();
      rings.children.forEach((child: THREE.Object3D) => {
        const mesh = child as THREE.Mesh;
        mesh.geometry.dispose();
        (mesh.material as THREE.Material).dispose();
      });
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);

  return (
    <section id="experience" ref={sectionRef} className="relative h-[300svh] bg-[#050505] text-white">
      <div className="sticky top-0 h-svh overflow-hidden">
        <div ref={mountRef} className="absolute inset-0" aria-hidden="true" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_15%,rgba(5,5,5,0.28)_60%,#050505_100%)]" />
      </div>

      <div className="pointer-events-none absolute inset-0">
        {[
          ["Shift.", "shape"],
          ["Move.", "motion"],
          ["Stay.", "memory"],
        ].map(([word, accent]) => (
          <div key={word} className="site-container flex h-svh items-end pb-16 sm:pb-20">
            <h2 className="text-[clamp(5rem,15vw,15rem)] font-semibold leading-[0.72] tracking-[-0.095em]">
              {word}
              <span className="ml-4 align-top text-[10px] font-medium uppercase tracking-[0.18em] text-[#c9ff3b] sm:text-xs">
                {accent}
              </span>
            </h2>
          </div>
        ))}
      </div>
    </section>
  );
}
