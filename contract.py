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
    def close_out(self):

    @external
    def vote(self, voter_token: abi.Asset, vote: abi.String):
        get_voter_holding = (AssetHolding.balance(Int(0), Txn.assets[0]),)
        return Seq(
            # assert that the asset in the foreignAssets array is the voter token
            Assert(voter_token.asset_id() == self.voter_token_id.get()),
            # assert that voter token is held by sender
            voter_token.holding(Txn.sender())
            .balance()
            .outputReducer(
                lambda value, has_value: Assert(And(has_value, value > Int(0)))
            ),
            # assert that voting period is active
            Assert(Global.latest_timestamp() >= self.vote_begin.get()),
            Assert(Global.latest_timestamp() < self.vote_end.get()),
            # increment yes or no based on vote
            If(vote.get() == Bytes("yes"))
            .Then(self.yes.set(self.yes.get() + Int(1)))
            .ElseIf(vote.get() == Bytes("no"))
            .Then(self.no.set(self.no.get() + Int(1)))
            .Else(Approve()),
        )

if __name__ == "__main__":
    DAO().dump("artifacts")
