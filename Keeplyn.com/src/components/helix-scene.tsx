"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

export function HelixScene() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const sceneCanvas = canvas;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        canvas,
        alpha: true,
        antialias: true,
        powerPreference: "high-performance",
      });
    } catch {
      return;
    }

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
    renderer.setClearColor(0x000000, 0);
    renderer.outputColorSpace = THREE.SRGBColorSpace;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x050505, 0.055);

    const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 100);
    camera.position.set(0, 0, 13.5);

    const helix = new THREE.Group();
    scene.add(helix);

    const count = 92;
    const sphereGeometry = new THREE.IcosahedronGeometry(0.105, 1);
    const sphereMaterial = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      emissive: 0x7568ff,
      emissiveIntensity: 0.42,
      metalness: 0.15,
      roughness: 0.34,
      vertexColors: true,
    });
    const beads = new THREE.InstancedMesh(sphereGeometry, sphereMaterial, count * 2);
    beads.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

    const dummy = new THREE.Object3D();
    const white = new THREE.Color(0xffffff);
    const violet = new THREE.Color(0x7568ff);
    const lime = new THREE.Color(0xc9ff3b);
    const rungPositions: number[] = [];

    for (let index = 0; index < count; index += 1) {
      const angle = index * 0.29;
      const y = (index - count / 2) * 0.145;
      const radius = 2.05 + Math.sin(index * 0.17) * 0.08;

      const first = new THREE.Vector3(Math.sin(angle) * radius, y, Math.cos(angle) * radius);
      const second = new THREE.Vector3(Math.sin(angle + Math.PI) * radius, y, Math.cos(angle + Math.PI) * radius);

      dummy.position.copy(first);
      dummy.scale.setScalar(index % 7 === 0 ? 1.65 : 1);
      dummy.updateMatrix();
      beads.setMatrixAt(index * 2, dummy.matrix);
      beads.setColorAt(index * 2, index % 11 === 0 ? lime : white);

      dummy.position.copy(second);
      dummy.scale.setScalar(index % 9 === 0 ? 1.5 : 1);
      dummy.updateMatrix();
      beads.setMatrixAt(index * 2 + 1, dummy.matrix);
      beads.setColorAt(index * 2 + 1, index % 5 === 0 ? violet : white);

      if (index % 4 === 0) {
        rungPositions.push(first.x, first.y, first.z, second.x, second.y, second.z);
      }
    }
    beads.instanceMatrix.needsUpdate = true;
    if (beads.instanceColor) beads.instanceColor.needsUpdate = true;
    helix.add(beads);

    const rungGeometry = new THREE.BufferGeometry();
    rungGeometry.setAttribute("position", new THREE.Float32BufferAttribute(rungPositions, 3));
    const rungMaterial = new THREE.LineBasicMaterial({
      color: 0x7568ff,
      transparent: true,
      opacity: 0.38,
      blending: THREE.AdditiveBlending,
    });
    const rungs = new THREE.LineSegments(rungGeometry, rungMaterial);
    helix.add(rungs);

    const knotGeometry = new THREE.TorusKnotGeometry(4.55, 0.018, 320, 12, 2, 5);
    const knotMaterial = new THREE.MeshBasicMaterial({
      color: 0x7568ff,
      transparent: true,
      opacity: 0.18,
      wireframe: true,
      blending: THREE.AdditiveBlending,
    });
    const knot = new THREE.Mesh(knotGeometry, knotMaterial);
    knot.rotation.set(0.55, 0.1, -0.25);
    scene.add(knot);

    const particleCount = 650;
    const particlePositions = new Float32Array(particleCount * 3);
    for (let index = 0; index < particleCount; index += 1) {
      const radius = 4 + Math.random() * 14;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      particlePositions[index * 3] = radius * Math.sin(phi) * Math.cos(theta);
      particlePositions[index * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      particlePositions[index * 3 + 2] = radius * Math.cos(phi);
    }
    const particleGeometry = new THREE.BufferGeometry();
    particleGeometry.setAttribute("position", new THREE.BufferAttribute(particlePositions, 3));
    const particleMaterial = new THREE.PointsMaterial({
      color: 0x8f87ff,
      size: 0.035,
      transparent: true,
      opacity: 0.72,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    const particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);

    scene.add(new THREE.AmbientLight(0xffffff, 1.4));
    const keyLight = new THREE.PointLight(0x7568ff, 42, 26, 2);
    keyLight.position.set(4, 4, 7);
    scene.add(keyLight);
    const rimLight = new THREE.PointLight(0xc9ff3b, 24, 22, 2);
    rimLight.position.set(-6, -3, 3);
    scene.add(rimLight);

    const pointer = new THREE.Vector2();
    let scrollProgress = 0;

    function updatePointer(event: PointerEvent) {
      pointer.x = event.clientX / window.innerWidth - 0.5;
      pointer.y = event.clientY / window.innerHeight - 0.5;
    }

    function updateScroll() {
      scrollProgress = window.scrollY / Math.max(window.innerHeight, 1);
    }

    window.addEventListener("pointermove", updatePointer, { passive: true });
    window.addEventListener("scroll", updateScroll, { passive: true });

    function resize() {
      const { clientWidth, clientHeight } = sceneCanvas;
      if (!clientWidth || !clientHeight) return;
      renderer.setSize(clientWidth, clientHeight, false);
      camera.aspect = clientWidth / clientHeight;
      camera.updateProjectionMatrix();
    }

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(sceneCanvas);
    resize();

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let frame = 0;

    function render(time = 0) {
      const elapsed = time * 0.001;
      helix.rotation.y = elapsed * 0.22 + scrollProgress * 0.38;
      helix.rotation.z = Math.sin(elapsed * 0.32) * 0.12;
      helix.rotation.x = -0.12 + pointer.y * 0.24;
      helix.position.x += (pointer.x * 0.7 - helix.position.x) * 0.035;
      knot.rotation.y = elapsed * -0.075;
      knot.rotation.z = elapsed * 0.04;
      particles.rotation.y = elapsed * 0.012;
      particles.rotation.x = elapsed * -0.008;
      camera.position.x += (pointer.x * 0.65 - camera.position.x) * 0.025;
      camera.position.y += (-pointer.y * 0.45 - camera.position.y) * 0.025;
      camera.lookAt(0, 0, 0);
      renderer.render(scene, camera);
      frame = window.requestAnimationFrame(render);
    }

    if (reducedMotion) {
      renderer.render(scene, camera);
    } else {
      render();
    }

    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", updatePointer);
      window.removeEventListener("scroll", updateScroll);
      resizeObserver.disconnect();
      sphereGeometry.dispose();
      sphereMaterial.dispose();
      rungGeometry.dispose();
      rungMaterial.dispose();
      knotGeometry.dispose();
      knotMaterial.dispose();
      particleGeometry.dispose();
      particleMaterial.dispose();
      renderer.dispose();
    };
  }, []);

  return <canvas ref={canvasRef} className="size-full" aria-hidden="true" />;
}
