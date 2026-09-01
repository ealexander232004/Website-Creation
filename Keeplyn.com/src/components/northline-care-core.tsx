"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

const NAVY = 0x173a5a;
const SKY = 0xbfe7f5;
const CORAL = 0xff725e;
const WHITE = 0xffffff;

export function NorthlineCareCore() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: "high-performance" });
    } catch {
      return;
    }

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.7));
    renderer.setClearColor(0x000000, 0);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.18;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(43, 1, 0.1, 40);
    camera.position.set(0, 0, 7.2);

    const system = new THREE.Group();
    system.rotation.set(-0.18, -0.22, 0.08);
    scene.add(system);

    const glass = new THREE.MeshPhysicalMaterial({
      color: SKY,
      metalness: 0.05,
      roughness: 0.08,
      transmission: 0.76,
      transparent: true,
      opacity: 0.9,
      thickness: 1.4,
      clearcoat: 1,
      clearcoatRoughness: 0.06,
    });
    const core = new THREE.Mesh(new THREE.IcosahedronGeometry(1.08, 5), glass);
    core.scale.set(1, 1.08, 0.82);
    system.add(core);

    const inner = new THREE.Mesh(
      new THREE.IcosahedronGeometry(0.56, 3),
      new THREE.MeshStandardMaterial({ color: CORAL, emissive: CORAL, emissiveIntensity: 1.35, roughness: 0.35 }),
    );
    system.add(inner);

    const ringMaterial = new THREE.MeshPhysicalMaterial({
      color: WHITE,
      emissive: SKY,
      emissiveIntensity: 0.5,
      metalness: 0.58,
      roughness: 0.2,
      transparent: true,
      opacity: 0.88,
      clearcoat: 1,
    });
    const ringConfigs = [
      { radius: 1.75, tube: 0.035, rotation: [1.08, 0.2, 0.32] },
      { radius: 2.18, tube: 0.026, rotation: [0.28, 1.02, -0.42] },
      { radius: 2.62, tube: 0.018, rotation: [1.32, -0.42, 0.72] },
    ] as const;
    const rings = ringConfigs.map((config) => {
      const ring = new THREE.Mesh(new THREE.TorusGeometry(config.radius, config.tube, 12, 180), ringMaterial);
      ring.rotation.set(config.rotation[0], config.rotation[1], config.rotation[2]);
      system.add(ring);
      return ring;
    });

    const smile = new THREE.Mesh(
      new THREE.TorusGeometry(1.38, 0.085, 18, 120, Math.PI * 1.18),
      new THREE.MeshStandardMaterial({ color: CORAL, emissive: CORAL, emissiveIntensity: 0.65, roughness: 0.32 }),
    );
    smile.rotation.set(0.1, 0.2, 0.92);
    smile.position.set(-0.04, -0.1, 0.84);
    system.add(smile);

    const satelliteGeometry = new THREE.SphereGeometry(0.09, 18, 18);
    const satelliteMaterial = new THREE.MeshStandardMaterial({ color: WHITE, emissive: SKY, emissiveIntensity: 0.65, roughness: 0.2 });
    const satellites = new THREE.Group();
    for (let index = 0; index < 12; index += 1) {
      const satellite = new THREE.Mesh(satelliteGeometry, index % 4 === 0
        ? new THREE.MeshStandardMaterial({ color: CORAL, emissive: CORAL, emissiveIntensity: 1, roughness: 0.25 })
        : satelliteMaterial);
      const angle = (index / 12) * Math.PI * 2;
      const radius = index % 2 === 0 ? 2.18 : 2.7;
      satellite.position.set(Math.cos(angle) * radius, Math.sin(angle * 1.7) * 1.42, Math.sin(angle) * radius * 0.45);
      satellite.scale.setScalar(index % 3 === 0 ? 1.5 : 1);
      satellites.add(satellite);
    }
    system.add(satellites);

    const pointCount = 320;
    const pointPositions = new Float32Array(pointCount * 3);
    for (let index = 0; index < pointCount; index += 1) {
      const angle = index * 2.39996;
      const radius = 2.9 + ((index * 37) % 100) / 78;
      pointPositions[index * 3] = Math.cos(angle) * radius;
      pointPositions[index * 3 + 1] = (((index * 53) % 100) / 100 - 0.5) * 5.8;
      pointPositions[index * 3 + 2] = Math.sin(angle) * radius - 1.4;
    }
    const pointsGeometry = new THREE.BufferGeometry();
    pointsGeometry.setAttribute("position", new THREE.BufferAttribute(pointPositions, 3));
    const points = new THREE.Points(pointsGeometry, new THREE.PointsMaterial({ color: NAVY, size: 0.022, transparent: true, opacity: 0.34 }));
    scene.add(points);

    scene.add(new THREE.HemisphereLight(WHITE, NAVY, 2.2));
    const coralLight = new THREE.PointLight(CORAL, 42, 18, 2);
    coralLight.position.set(-3.6, 2.6, 5.2);
    scene.add(coralLight);
    const skyLight = new THREE.PointLight(SKY, 54, 20, 2);
    skyLight.position.set(4.2, -2.2, 4.4);
    scene.add(skyLight);

    const pointer = new THREE.Vector2();
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let frame = 0;
    let previousTime = 0;

    const handlePointerMove = (event: PointerEvent) => {
      const bounds = canvas.getBoundingClientRect();
      pointer.x = ((event.clientX - bounds.left) / Math.max(bounds.width, 1) - 0.5) * 2;
      pointer.y = ((event.clientY - bounds.top) / Math.max(bounds.height, 1) - 0.5) * 2;
    };

    const handlePointerLeave = () => pointer.set(0, 0);

    const resize = () => {
      const width = canvas.clientWidth;
      const height = canvas.clientHeight;
      if (!width || !height) return;
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.position.z = width < 560 ? 8.2 : 7.2;
      camera.updateProjectionMatrix();
    };

    const observer = new ResizeObserver(resize);
    observer.observe(canvas);
    canvas.addEventListener("pointermove", handlePointerMove);
    canvas.addEventListener("pointerleave", handlePointerLeave);
    resize();

    const render = (time = 0) => {
      const delta = Math.min((time - previousTime) / 1000 || 0, 0.05);
      previousTime = time;
      if (!reducedMotion) {
        system.rotation.y += delta * 0.2;
        satellites.rotation.z -= delta * 0.12;
        rings[0].rotation.z += delta * 0.11;
        rings[1].rotation.x -= delta * 0.08;
        rings[2].rotation.y += delta * 0.06;
        inner.scale.setScalar(1 + Math.sin(time * 0.0015) * 0.06);
      }
      system.rotation.x += ((-0.18 - pointer.y * 0.12) - system.rotation.x) * 0.035;
      system.rotation.z += ((0.08 + pointer.x * 0.08) - system.rotation.z) * 0.035;
      points.rotation.y = reducedMotion ? 0 : time * 0.000012;
      renderer.render(scene, camera);
      frame = window.requestAnimationFrame(render);
    };
    render();

    return () => {
      window.cancelAnimationFrame(frame);
      observer.disconnect();
      canvas.removeEventListener("pointermove", handlePointerMove);
      canvas.removeEventListener("pointerleave", handlePointerLeave);
      const geometries = new Set<THREE.BufferGeometry>();
      const materials = new Set<THREE.Material>();
      scene.traverse((object) => {
        if (object instanceof THREE.Mesh || object instanceof THREE.Points) {
          geometries.add(object.geometry);
          const objectMaterials = Array.isArray(object.material) ? object.material : [object.material];
          objectMaterials.forEach((material) => materials.add(material));
        }
      });
      geometries.forEach((geometry) => geometry.dispose());
      materials.forEach((material) => material.dispose());
      renderer.dispose();
    };
  }, []);

  return <canvas ref={canvasRef} className="northline-care-core size-full" data-visual="three-dimensional-care-core" aria-hidden="true" />;
}
