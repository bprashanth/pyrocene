// Facilitator copy. Edit these short paragraphs without changing the game.
import CONFIG from './round-config.json' with {type:'json'};
export const BRIEFINGS={
 negligence:{
  removal:{title:'Return after six months.',paragraphs:['Weeds are growing among your planted trees. Clearing a new patch pays more. Careful weeding among saplings costs more and returns less.','Select a patch and move the projection slider. Compare With removal and Without removal. Unplanted ground can fill with invasives again.','Both teams propose where to send one crew. The room must agree on one patch.']},
  ecology:{title:'Protect what you planted.',paragraphs:CONFIG.extensions.seedStudy?['Six months have passed. Why are weeds returning? In Close view, open Seeds to compare a grass with a native tree.','Compare seed arrival with growing conditions. Then use the projection and structure view to judge what needs care.','Propose one patch for follow-up. Explain your findings to the removal team. Agree where the crew goes.']:['Six months have passed. Weeds are returning among your young trees. New clearing brings income but leaves those trees without care.','Compare With removal and Without removal, then examine the structure. These are practice forecasts.','Propose one patch for follow-up. Both teams must agree where the crew goes.']},
  room:{title:'One crew. One choice.',paragraphs:['The first plan is already planted. Six months later, the crew can weed among those trees or clear a new patch.','Compare the return with the planted trees that could be lost. Use the year slider and structure view before committing.','Both teams must agree on one follow-up patch.']}
 },
 ecology:{title:'Choose where to restore.',paragraphs:[
  'Examine the three patches. Choose one to restore. Compare its cost and the forest health it could recover.',
  'Use the close view and structure lab to make your choice. Be ready to explain it to the room. Propose ends your turn.',
  'When both teams are ready, the room agrees where to remove and restore.'
 ]},
 removal:{title:'Choose where to remove.',paragraphs:[
  'Examine the three patches. Choose one for invasive removal. Compare the cost, the return and the damage to native growth.',
  'Use the close view and structure lab to make your choice. Be ready to explain it to the room. Propose ends your turn.',
  'When both teams are ready, the room agrees where to remove and restore.'
 ]},
 room:{title:'Bring the plans together.',paragraphs:[
  'Both teams examine the same forest and propose one patch each.',
  'Reveal their choices. Ask each group to explain its proposal. Compare costs, returns and forest health. Teams can revise before you commit.',
  'Commit one shared plan. Change the recovery year and move the fire forward to see what the plan changes.'
 ]}
};
