#!/usr/bin/env python3
from pyteal import *
from beaker import *
import os
import json
from typing import Final


class DAO(Application):
    # global byte 1 - key for the creator address
    Creator: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.bytes, default=Global.creator_address()
    )

    # global int 1 - key for the registration begin round
    RegBegin: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64, default=Int(0)
    )

    # global int 2 - key for the registration end round
    RegEnd: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64, default=Int(0)
    )

    # global int 3 - key for the voting begin round
    VoteBegin: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64, default=Int(0)
    )

    # global int 4 - key for the voting end round
    VoteEnd: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64, default=Int(0)
    )

    # global int 5 - asset id of the voter token
    voter_token: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64, default=Int(0)
    )

    # global int 6 - integer key for the number of yes votes
    yes: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64, default=Int(0)
    )

    # global int 7 - interger key for the number of no votes
    no: Final[ApplicationStateValue] = ApplicationStateValue(
        stack_type=TealType.uint64, default=Int(0)
    )

    # local byte 1 - key for the vote of the voter
    vote: Final[AccountStateValue] = AccountStateValue(
        stack_type=TealType.bytes, default=Bytes("")
    )

    # local int 1 - key for if voter has voted
    voted: Final[AccountStateValue] = AccountStateValue(
        stack_type=TealType.uint64, default=Int(0)
    )

    @create
    def create(self, voter_token: abi.Asset):
        return Seq(
            Assert(Txn.application_args.length() == Int(4)),
            self.initialize_application_state(),
            self.RegBegin.set(Txn.application_args[0]),
            self.RegEnd.set(Txn.application_args[1]),
            self.VoteBegin.set(Txn.application_args[2]),
            self.VoteEnd.set(Txn.application_args[3]),
            self.voter_token.set(voter_token.asset_id()),
        )

    @opt_in
    def opt_in(self):
        return Seq(
            And(
                Global.round() >= App.globalGet(Bytes("RegBegin")),
                Global.round() <= App.globalGet(Bytes("RegEnd")),
            )
        )
    
    @close_out
    def close_out(self, voter_token: abi.Asset):
        get_token_holding = (AssetHolding.balance(Int(0), Txn.assets[0]))
        return Seq(
            [
                get_token_holding,
                If(
                    And(
                        Global.round() <= App.globalGet(Bytes("VoteEnd")),
                        get_token_holding.hasValue(),
                    ),
                    If(App.localGet(Int(0), Bytes("vote")) == Bytes("Yes"))
                    .Then(App.globalPut(Bytes("YesCount"), App.globalGet(Bytes("YesCount")) - get_token_holding.value()))
                    .ElseIf(App.localGet(Int(0), Bytes("vote")) == Bytes("No"))
                    .Then(App.globalPut(Bytes("NoCount"), App.globalGet(Bytes("NoCount")) - get_token_holding.value()))
                    .ElseIf(App.localGet(Int(0), Bytes("vote")) == Bytes("Abstain"))
                    .Then(Return(Int(1))),
                ),
                Return(Int(1)),
            ]
        )

    @external
    def vote(self, voter_token: abi.Asset, vote: abi.String):
        get_token_holding = (AssetHolding.balance(Int(0), Txn.assets[0]))
        return Seq(
            [
                App.globalPut(Bytes("vote"), Txn.application_args[1]),
                get_token_holding,
                If(
                    And(
                        Global.round() >= App.globalGet(Bytes("VoteBegin")),
                        Global.round() <= App.globalGet(Bytes("VoteEnd")),
                        get_token_holding.hasValue(),
                        Or(
                            App.localGet(Int(0), Bytes("vote")) == Bytes("Yes"),
                            App.localGet(Int(0), Bytes("vote")) == Bytes("No"),
                            App.localGet(Int(0), Bytes("vote")) == Bytes("Abstain"),
                        ),
                    ),
                    If(App.localGet(Int(0), Bytes("vote")) == Bytes("Yes"))
                    .Then(App.globalPut(Bytes("YesCount"), App.globalGet(Bytes("YesCount")) + get_token_holding.value()))
                    .ElseIf(App.localGet(Int(0), Bytes("vote")) == Bytes("No"))
                    .Then(App.globalPut(Bytes("NoCount"), App.globalGet(Bytes("NoCount")) + get_token_holding.value()))
                    .ElseIf(App.localGet(Int(0), Bytes("vote")) == Bytes("Abstain"))
                    .Then(Return(Int(1))),
                ),
                Return(Int(1)),
            ]
        )

if __name__ == "__main__":
    DAO().dump("artifacts")
