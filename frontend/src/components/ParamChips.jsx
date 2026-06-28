const ORDER = ["aggression", "openness", "creativity", "confidence", "cooperation"];
const LABELS = {
  aggression: "Aggress.", openness: "Openness", creativity: "Creativ.",
  confidence: "Confid.", cooperation: "Cooperat.",
};

export default function ParamChips({ params }) {
  if (!params) return null;
  return (
    <>
      {ORDER.map((k) => {
        const lvl = params[k].level;
        const cls = "lv-" + lvl.replace(/\s+/g, "-");
        return (
          <div className={"chip " + cls} key={k}>
            <span className="lbl">{LABELS[k]}</span>
            <span className="val">{lvl}</span>
          </div>
        );
      })}
    </>
  );
}
