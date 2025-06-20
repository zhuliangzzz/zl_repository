#! /usr/bin/perl
#### write by hyp, Dec 11, 2017
use strict;
use utf8;
use Tk;

my $mw = MainWindow->new( -title => "PID:$$" );
${mw}->geometry("+400+250");
my $text = $mw->Text(
    -background       => 'white',
    -foreground       => "blue",
    -font             => 'monospace 18 bold',
    -width            => 40,
    -selectforeground => 'yellow',
    -relief           => 'sunken',
    -spacing1         => 16,
    -height           => 3,
)->pack( -expand => 1, -fill => 'both' );
$text->insert( 'end', "警告:\n将检查并修复InCAM的joblist文件，是否继续？");
$text->configure(-state => 'disable');

my $frame1 = $mw->Frame->pack( -side => 'bottom' , -expand => 1 );
my $continueButton = $frame1->Button(
    -text             => '继续',
    -font             => [ -size => 10 ],
    -width            => '10',
    -height           => '2',
    -activebackground => 'green',
    -command => sub { 
        print "continue";
        $mw->destroy;
        exit 0;
    }
)->pack( -side => "left", -padx => "100", -pady => "2" );

my $cancelButton = $frame1->Button(
    -text             => '取消',
    -font             => [ -size => 10 ],
    -width            => '10',
    -height           => '2',
    -activebackground => 'green',
    -command => sub { 
        print "cancel";
        $mw->destroy;
        exit 0;
    }
)->pack( -side => "left", -padx => "100", -pady => "2" );

MainLoop;
