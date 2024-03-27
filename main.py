from pokerkit import Automation, NoLimitTexasHoldem


class Poker():
    def __init__(self, players: dict, player_ids: dict, bb: int):
        self.bb = bb
        self.starting_balance = {}
        self.player_ids = player_ids
        self.players = len(players.keys())
        self.player_grid = players
        self.all_stacks = []
        self.blinds = None
        self.state = None
        for player_id, row_key in enumerate(self.player_grid):
            balance = self.player_grid[row_key]
            self.all_stacks.append(balance)
        self.set_starting_stacks()

    def get_starting_balance(self):
        return self.starting_balance
    def set_starting_stacks(self):

        min_bet = self.bb
        antes = (int(self.bb / 4))
        if self.blinds is not None:
            blinds_or_straddles = (int(self.bb / 2), self.bb)
        else:
            blinds_or_straddles = ()
        self.state = NoLimitTexasHoldem.create_state(
            # Automations
            (
                Automation.ANTE_POSTING,
                Automation.BET_COLLECTION,
                Automation.BLIND_OR_STRADDLE_POSTING,
                Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
                Automation.HAND_KILLING,
                Automation.CHIPS_PUSHING,
                Automation.CHIPS_PULLING,
            ),
            True,  # Uniform antes?
            antes,  # Antes
            blinds_or_straddles,  # Blinds or straddles
            min_bet,  # Min-bet
            self.all_stacks,  # Starting stacks
            self.players,  # Number of players
        )

    def pay_blinds(self, blinds: tuple):
        self.blinds = blinds
        for i in range(len(blinds)):
            blind = blinds[i]
            player_id = f"player{str(i)}"
            print(f"Blinds paid of {blind} by {self.player_ids[player_id]}")
        self.set_starting_stacks()
        print(f"After Blinds: {self.get_stacks()}")



    def set_sitout_players(self, sitout: list):
        for playerid in sitout:
            self.player_grid.pop(playerid)
        return True

    def current_players(self):
        return self.player_grid

    def get_stacks(self, init = False):
        all_stacks = self.state.stacks  # [572100, 1997500, 1109500]
        output = {}
        for player_id, row_key in enumerate(self.player_grid):
            output[self.player_ids[row_key]] = all_stacks[player_id]
        if init:
            self.starting_balance = output
        return output

    def money_in_pot(self):
        starting_balances = self.starting_balance
        current_balances = self.get_stacks()
        output = {}
        for player in current_balances:
            output[player] = int( starting_balances[player] - current_balances[player])
        return output

    def pre_deal(self, specific_hands: dict):
        print("\nRound 0:")
        print(f"Initial Stacks: {self.get_stacks(init=True)}")
        self.pay_blinds(blinds=tuple([1000, 2000]))
        self.start_hand(specific_hands=specific_hands)

    def start_hand(self, specific_hands: dict):
        if self.blinds is None:
            print("Blinds need to be paid first")
            return False
        print("\n\n*** Dealing Cards ***\n\n")
        for player_id, row_key in enumerate(self.player_grid):
            if row_key in list(specific_hands.keys()):
                hand_to_deal = specific_hands[row_key]
                print(f"{self.player_ids[row_key]}: {hand_to_deal}")
                print(f"{self.player_ids[row_key]}: {self.state.deal_hole(hand_to_deal)}\n")
            else:
                self.state.deal_hole('????')  # Antonius
        print("\n\n*** Card Dealing Ends ***\n\n")
        return True

    def get_final_decision(self):
        output = {}
        for player_id, row_key in enumerate(self.player_grid):
            resp = self.state.get_hand(player_id, 0)
            print(resp)
            output[row_key] = resp
        return output

    def get_winners(self):
        winners = self.get_final_decision()
        output = {}
        for key in winners:
            output[self.player_ids[key]] = winners[key]
        return output

    def deal_flops(self, cards):
        try:
            burn_card = self.state.burn_card('??')
            print("\n\n*** Dealing Flops ***\n\n")
            print(burn_card)
            print(self.state.deal_board(cards))
            print("\n\n*** Card Dealing Ends ***\n\n")
            print(f"Stacks on Flops : {self.get_stacks()}")
            print(f"Money in Pot: {self.money_in_pot()}")
            return True
        except:
            return False

    def deal_turn(self, cards):
        try:
            burn_card = self.state.burn_card('??')
            print("\n\n*** Dealing Turn ***\n\n")
            print(burn_card)
            print(self.state.deal_board(cards))
            print("\n\n*** Card Dealing Ends ***\n\n")
            print(f"Stacks on Turn: {self.get_stacks()}")
            print(f"Money in Pot: {self.money_in_pot()}")
            return True
        except:
            return False

    def deal_river(self, cards):
        try:
            burn_card = self.state.burn_card('??')
            print("\n\n*** Dealing River ***\n\n")
            print(burn_card)
            print(self.state.deal_board(cards))
            print("\n\n*** Card Dealing Ends ***\n\n")
            print(f"Stacks on River: {self.get_stacks()}")
            print(f"Money in Pot: {self.money_in_pot()}")
            return True
        except:
            return False


def process_bet(pk, bet_or_check_or_fold: int):
    try:
        print(bet_or_check_or_fold)
        resp = pk.state.complete_bet_or_raise_to(bet_or_check_or_fold)  # Dwan
        print(resp)
        return True
    except ValueError as e:
        print(f"You cannot bet less than {e}")
        return False


def prepare(all_players, player_ids, community_cards: dict,
            specific_hands: dict, sit_outs: list, bb=2000):
    cards_for_flop = community_cards["flop"]
    cards_for_turn = community_cards["turn"]
    cards_for_river = community_cards["river"]
    cards_for_flop = "".join(cards_for_flop)
    cards_for_turn = "".join(cards_for_turn)
    cards_for_river = "".join(cards_for_river)
    pk = Poker(players=all_players, player_ids=player_ids, bb=bb)
    pk.pre_deal(specific_hands=specific_hands)
    counter = 0
    flop_dealt, turn_dealt, river_dealt = False, False, False
    folded_players = []
    loop = 100
    all_player_ids = []
    for i in range(loop):
        for key in player_ids.keys():
            all_player_ids.append(key)
    main_flag = True
    while main_flag:
        if not main_flag:
            break
        for id in all_player_ids:
            if not main_flag:
                break
            counter += 1
            if counter < 3:
                continue
            if id in folded_players:
                continue
            name = player_ids[id]
            # name = player_ids[val]
            temp_flag = True
            while temp_flag:
                try:
                    bcf = int(input(f"\n{name.title()}: "))
                    temp_flag = False
                    if bcf < 0:
                        print("Fold")
                        print(pk.state.fold())  # Antonius
                        folded_players.append(id)
                        continue
                    if bcf == 0:
                        print("Check or Call")
                        print(pk.state.check_or_call())  # Antonius
                        continue
                    print("Process")
                    while not process_bet(pk, bcf):
                        try:
                            bcf = int(input(f"\n{name.title()}: "))
                        except:
                            continue
                    print("Call")

                except:
                    continue
            if counter % 3 == 0:
                try:
                    if not flop_dealt:
                        flop_dealt = pk.deal_flops(cards=cards_for_flop)
                        continue
                    if not turn_dealt:
                        turn_dealt = pk.deal_turn(cards=cards_for_turn)
                        continue
                    if not river_dealt:
                        river_dealt = pk.deal_river(cards=cards_for_river)
                        continue
                    if flop_dealt and turn_dealt and river_dealt:
                        main_flag = False
                        break
                except Exception as e:
                    pass
    print(f"Final stacks after pre-flop: {pk.get_stacks()}\n\n")
    print(pk.get_winners())
    return True



if __name__ == "__main__":

    fair = False
    players = [
        {
            "name": "ivey",
            "balance": 1125600,
            # "deal": "Ac2d",
            "deal": "????"
        },
        {
            "name": "antonius",
            "balance": 2000000,
            "deal": "????"
        },
        {
            "name": "dwan",
            "balance": 553500,
            # "deal": "7h6h",
            "deal": "????"
        }
    ]
    community_cards = {
        "flop": ['??', '??', '??'],
        "turn": ['??'],
        "river": ['??']
    }

    # community_cards = {
    #     "flop": ['Jc', '3d', '5c'],
    #     "turn": ['4h'],
    #     "river": ['Jh']
    # }
    all_players, player_ids, specific_hands = {}, {}, {}
    counter = 0
    for row in players:
        all_players["player" + str(counter)] = row["balance"]
        player_ids["player" + str(counter)] = row["name"]
        specific_hands["player" + str(counter)] = row["deal"]
        counter += 1
    # print(all_players)
    sit_outs = []
    bb = 2000
    loop_break = False
    while not loop_break:
        if prepare(all_players=all_players, player_ids=player_ids,
                   community_cards=community_cards,
                   specific_hands=specific_hands, sit_outs=sit_outs, bb=bb):
            repeat = input("Do you want another hand dealt? (y/n) (default: n): ")
            if repeat.lower() == "y":
                print("\n\n")
                continue
            else:
                break


