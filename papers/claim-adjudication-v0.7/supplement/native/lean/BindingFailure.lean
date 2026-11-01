import Std

/- Candidate formalization of the pointwise gluing lemma. This source was
   NOT compiled in the preparation environment. It contains no `sorry` or
   result axiom. Checking it with Lean is an outstanding review action.
   The observation quotient and global decoder equivalence are outside this
   file: they remain explicit assumptions/arguments in the manuscript. -/

namespace Witnessability

abbrev Record (I A : Type) := I → A
abbrev Fault (I : Type) := I → Prop

structure Binding (I A : Type) where
  forward : I → A → A
  reverse : I → A → A
  leftInverse : ∀ i x, reverse i (forward i x) = x
  rightInverse : ∀ i x, forward i (reverse i x) = x

def HonestOutside {I A : Type} (F : Fault I) (u r : Record I A) : Prop :=
  ∀ i, ¬ F i → u i = r i

def Covered {I A : Type} (b : Binding I A) (F₀ F₁ : Fault I)
    (r₀ r₁ : Record I A) : Prop :=
  ∀ i, r₀ i ≠ b.forward i (r₁ i) → F₀ i ∨ F₁ i

theorem common_representatives_imply_cover {I A : Type}
    (b : Binding I A) (F₀ F₁ : Fault I) (r₀ r₁ u v : Record I A)
    (hu : HonestOutside F₀ u r₀) (hv : HonestOutside F₁ v r₁)
    (he : ∀ i, u i = b.forward i (v i)) : Covered b F₀ F₁ r₀ r₁ := by
  intro i hne
  by_cases h₀ : F₀ i
  · exact Or.inl h₀
  by_cases h₁ : F₁ i
  · exact Or.inr h₁
  exfalso
  apply hne
  calc
    r₀ i = u i := (hu i h₀).symm
    _ = b.forward i (v i) := he i
    _ = b.forward i (r₁ i) := congrArg (b.forward i) (hv i h₁)

noncomputable def blend {I A : Type} (b : Binding I A) (F₀ : Fault I)
    (r₀ r₁ : Record I A) : Record I A := by
  classical
  exact fun i => if F₀ i then b.forward i (r₁ i) else r₀ i

theorem cover_implies_common_representatives {I A : Type}
    (b : Binding I A) (F₀ F₁ : Fault I) (r₀ r₁ : Record I A)
    (hc : Covered b F₀ F₁ r₀ r₁) :
    ∃ u v, HonestOutside F₀ u r₀ ∧ HonestOutside F₁ v r₁ ∧
      (∀ i, u i = b.forward i (v i)) := by
  classical
  let u := blend b F₀ r₀ r₁
  let v : Record I A := fun i => b.reverse i (u i)
  refine ⟨u, v, ?_, ?_, ?_⟩
  · intro i hn
    simp [u, blend, hn]
  · intro i hn
    by_cases h₀ : F₀ i
    · simpa [v, u, blend, h₀] using b.leftInverse i (r₁ i)
    · have hr : r₀ i = b.forward i (r₁ i) := by
        by_contra hne
        rcases hc i hne with hf | hf
        · exact h₀ hf
        · exact hn hf
      simpa [v, u, blend, h₀, hr] using b.leftInverse i (r₁ i)
  · intro i
    exact (b.rightInverse i (u i)).symm

theorem gluing_iff_cover {I A : Type}
    (b : Binding I A) (F₀ F₁ : Fault I) (r₀ r₁ : Record I A) :
    (∃ u v, HonestOutside F₀ u r₀ ∧ HonestOutside F₁ v r₁ ∧
      (∀ i, u i = b.forward i (v i))) ↔ Covered b F₀ F₁ r₀ r₁ := by
  constructor
  · rintro ⟨u, v, hu, hv, he⟩
    exact common_representatives_imply_cover b F₀ F₁ r₀ r₁ u v hu hv he
  · exact cover_implies_common_representatives b F₀ F₁ r₀ r₁

#print axioms gluing_iff_cover

end Witnessability
