import {negligenceEnabled} from './game-features.mjs';
await import(negligenceEnabled?'./round.mjs':'./cooperation.mjs');
