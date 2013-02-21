# -*- coding: utf-8 -*-
from .baseclasses import *
from ..actions import *
from ..cards import *

from ..thbraid import use_faith


class FateSpear(Skill):
    associated_action = None
    target = t_None


class FateSpearAction(GenericAction):
    def __init__(self, act):
        self.act = act
        self.source = act.source
        self.target = act.target

    def apply_action(self):
        self.act.__class__ = InevitableAttack
        return True


class FateSpearHandler(EventHandler):
    execute_after = ('HakuroukenEffectHandler', )
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, BaseAttack):
            src = act.source
            if not src.has_skill(FateSpear): return act
            tgt = act.target

            while True:
                if tgt.life > src.life: break
                if len(tgt.cards) + len(tgt.showncards) < len(src.cards) + len(src.showncards): break
                return act

            if user_choose_option(self, act.source):
                Game.getgame().process_action(FateSpearAction(act))

        return act


class VampireKiss(Skill):
    associated_action = None
    target = t_None


class VampireKissAction(GenericAction):
    def apply_action(self):
        return Game.getgame().process_action(
            Heal(self.target, self.source)
        )


class VampireKissHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_apply' and isinstance(act, Damage):
            src, tgt = act.source, act.target
            if not (src and src.has_skill(VampireKiss)): return act
            if src.life >= src.maxlife: return act
            g = Game.getgame()
            pact = g.action_stack[-1]
            if not isinstance(pact, Attack): return act
            card = pact.associated_card
            if (not card) or card.color != Card.RED: return act
            g.process_action(VampireKissAction(src, tgt))

        return act


class HeartBreakAction(InevitableAttack):
    def __init__(self, source, target):
        self.source = source
        self.target = target
        self.amount = 2

    def apply_action(self):
        use_faith(self.target, 4)
        return InevitableAttack.apply_action(self)


class HeartBreak(Skill):
    associated_action = HeartBreakAction
    target = t_OtherOne

    @property
    def color(self):
        return Card.RED

    def is_card(self, cls):
        if issubclass(AttackCard, cls): return True
        return isinstance(self, cls)

    def check(self):
        if self.associated_cards: return False
        return len(self.player.faiths) >= 4


class NeverNightAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        tgt = self.target
        for p in self.target_list:
            if not (p.cards or p.showncards or p.equips):
                if p.faiths:
                    g.process_action(DropCards(p, p.faiths))
            else:
                cats = [p.cards, p.showncards, p.equips]
                c = choose_peer_card(tgt, p, cats)
                if not c:
                    c = random_choose_card(cats)

                g.process_action(DropCards(p, [c]))

        return True


class NeverNight(Skill):
    associated_action = NeverNightAction
    target = t_All

    def check(self):
        if self.associated_cards: return False
        return len(self.player.faiths) >= 4


class ScarletFogAction(UserAction):
    def apply_action(self):
        g = Game.getgame()
        src = self.source
        tags = src.tags
        tags['scarletfog_tag'] = tags['turn_count']

        for p in self.target_list:
            _pl = g.attackers[:]
            _pl.remove(p)
            pl = []
            atkcard = AttackCard()
            for t in _pl:
                if LaunchCard(p, [t], atkcard).can_fire():
                    pl.append(t)

            rst = user_choose_cards_and_players(self, p, [p.cards, p.showncards], pl)
            if rst:
                c = rst[0][0]; t = rst[1][0]
                g.process_action(LaunchCard(p, t, c))
            else:
                g.process_action(LifeLost(p, p, 1))

        return True

    def cond(self, cl):
        return len(cl) == 1 and cl[0].is_card(AttackCard)

    def choose_player_target(self, tl):
        if not tl:
            return (tl, False)

        return (tl[-1:], True)

    def is_valid(self):
        tags = self.source.tags
        return tags['turn_count'] > tags['scarletfog_tag']


class ScarletFog(Skill):
    associated_action = ScarletFogAction
    target = t_All
    def check(self):
        cl = self.associated_cards
        if not len(cl) == 1: return False
        c = cl[0]
        if c.is_card(VirtualCard): return False
        if c.color != Card.RED: return False
        return True


class QueenOfMidnight(Skill):
    associated_action = None
    target = t_None


class QueenOfMidnightHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_before' and isinstance(act, ActionStage):
            g = Game.getgame()
            tgt = act.target
            if not tgt.has_skill(QueenOfMidnight): return act
            g.process_action(DrawCards(act.target, 2))

        elif evt_type == 'action_before' and isinstance(act, DropCardStage):
            tgt = act.target
            if tgt.has_skill(QueenOfMidnight):
                act.dropn = max(act.dropn - 2, 0)

        return act


class Septet(Skill):
    associated_action = None
    target = t_None


class SeptetHandler(EventHandler):
    def handle(self, evt_type, act):
        if evt_type == 'action_after' and isinstance(act, DelayedSpellCardAction):
            src = act.source
            tgt = act.target
            if not src.has_skill(Septet): return act
            self.action = act
            c = user_choose_cards(self, src, [src.cards, src.showncards])
            g = Game.getgame()
            if c:
                g.process_action(DropCards(src, [c]))
            else:
                g.process_action(DropCards(tgt, [act.card]))

        return act


class RemiliaEx2(Character):
    maxlife = 6
    maxfaith = 4
    skills = [
        HeartBreak,
        NeverNight,
        VampireKiss,
        FateSpear,
        ScarletFog,
        QueenOfMidnight,
        Septet,
    ]

    eventhandlers_required = [
        FateSpearHandler,
        VampireKissHandler,
        QueenOfMidnightHandler,
        SeptetHandler,
    ]

    initial_equips = [(GungnirCard, SPADE, Q)]


@register_ex_character
class RemiliaEx(Character):
    maxlife = 6
    maxfaith = 4
    skills = [HeartBreak, NeverNight, VampireKiss]
    eventhandlers_required = [VampireKissHandler]

    initial_equips = [(GungnirCard, SPADE, Q)]
    stage2 = RemiliaEx2
